"""
FinTrack AI - Machine Learning Engine
Handles: Transaction Categorization, Expense Prediction,
         Savings Recommendations, Spending Insights, AI Chatbot
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import json


# ─── 1. AI Transaction Categorizer ────────────────────────────────────────────

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "zomato", "swiggy", "restaurant", "cafe", "food", "pizza", "burger",
        "mcdonalds", "kfc", "dominos", "hotel", "dhaba", "biryani", "chai",
        "coffee", "snack", "lunch", "dinner", "breakfast", "meal", "eat",
        "kitchen", "tiffin", "dine", "eatery", "bakery", "sweet", "juice"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "meesho", "ajio", "nykaa", "market",
        "shop", "store", "purchase", "buy", "order", "clothes", "dress",
        "shoes", "bag", "watch", "accessory", "fashion", "retail", "mall",
        "bazaar", "grocery", "supermarket", "dmart", "reliance", "big bazaar"
    ],
    "Transportation": [
        "ola", "uber", "rapido", "auto", "cab", "taxi", "metro", "bus",
        "train", "railway", "irctc", "fuel", "petrol", "diesel", "parking",
        "toll", "flight", "indigo", "spicejet", "air india", "travel", "ride",
        "rickshaw", "bike", "vehicle", "transport"
    ],
    "Entertainment": [
        "netflix", "amazon prime", "hotstar", "spotify", "youtube", "movie",
        "cinema", "pvr", "inox", "bookmyshow", "concert", "event", "game",
        "gaming", "steam", "playstation", "subscription", "ott", "zee5",
        "disney", "hulu", "music", "show", "ticket","prime video"
    ],
    "Utilities": [
        "electricity", "water", "gas", "internet", "broadband", "wifi",
        "jio", "airtel", "vodafone", "bsnl", "mobile", "recharge", "bill",
        "utility", "maintenance", "rent", "housing", "electricity board",
        "bescom", "tata power", "dth", "tatasky"
    ],
    "Healthcare": [
        "hospital", "clinic", "doctor", "medicine", "pharmacy", "medical",
        "health", "lab", "test", "diagnostic", "apollo", "fortis",
        "1mg", "netmeds", "pharmeasy", "consultation", "surgery", "dental",
        "eye", "optician", "ayurveda", "homeopathy", "insurance"
    ],
    "Education": [
        "college", "university", "school", "course", "fee", "tuition",
        "book", "stationery", "pen", "notebook", "udemy", "coursera",
        "skill", "training", "coaching", "exam", "certification", "library",
        "assignment", "project", "study", "class", "workshop"
    ],
    "Travel": [
        "hotel", "resort", "oyo", "makemytrip", "goibibo", "booking",
        "airbnb", "yatra", "trip", "tour", "vacation", "holiday",
        "sightseeing", "trek", "adventure", "baggage"
    ],
}


def categorize_transaction(description: str, amount: float = 0, txn_type: str = "expense") -> str:
    """
    Rule-based + weighted keyword ML categorizer.
    Uses TF-style keyword scoring with amount heuristics.
    """
    if txn_type == "income":
        return "Income"

    desc_lower = description.lower()

    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in desc_lower:
                # Longer keyword matches score higher (more specific)
                score += len(kw.split())
        if score > 0:
            scores[cat] = score

    if not scores:
        # Amount-based fallback heuristics
        if amount < 200:
            return "Food & Dining"
        elif amount < 1000:
            return "Shopping"
        elif amount > 10000:
            return "Utilities"
        return "Other"

    return max(scores, key=scores.get)


# ─── 2. Expense Predictor (Linear Regression + Trend Analysis) ────────────────

def predict_future_expenses(df: pd.DataFrame) -> dict:
    """
    Predicts next 3 months of expenses per category
    using linear regression on historical monthly data.
    """
    if df.empty:
        return {"predictions": [], "total_predicted": 0}

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")

    monthly = df.groupby(["month", "category"])["amount"].sum().reset_index()
    monthly["month_idx"] = monthly["month"].rank(method="dense").astype(int)

    predictions = []
    categories = monthly["category"].unique()
    now = datetime.now()

    for cat in categories:
        cat_data = monthly[monthly["category"] == cat].sort_values("month_idx")
        if len(cat_data) < 2:
            continue

        x = cat_data["month_idx"].values.reshape(-1, 1)
        y = cat_data["amount"].values

        # Simple least squares linear regression
        x_mean, y_mean = x.mean(), y.mean()
        beta = np.sum((x.flatten() - x_mean) * (y - y_mean)) / np.sum((x.flatten() - x_mean) ** 2)
        alpha = y_mean - beta * x_mean

        max_idx = cat_data["month_idx"].max()
        future_months = []
        for i in range(1, 4):
            pred_idx = max_idx + i
            pred_val = max(0, alpha + beta * pred_idx)
            month_label = (now + timedelta(days=30 * i)).strftime("%b %Y")
            future_months.append({"month": month_label, "predicted": round(pred_val, 2)})

        # Trend direction
        if beta > 50:
            trend = "↑ Rising"
        elif beta < -50:
            trend = "↓ Falling"
        else:
            trend = "→ Stable"

        predictions.append({
            "category": cat,
            "avg_monthly": round(float(y.mean()), 2),
            "trend": trend,
            "next_months": future_months,
            "confidence": min(95, max(60, int(70 + len(cat_data) * 5)))
        })

    # Total prediction for next month
    total_next = sum(
        p["next_months"][0]["predicted"]
        for p in predictions
        if p["next_months"]
    )

    return {
        "predictions": sorted(predictions, key=lambda x: x["avg_monthly"], reverse=True),
        "total_predicted_next_month": round(total_next, 2)
    }


# ─── 3. Savings Recommender ────────────────────────────────────────────────────

def generate_savings_recommendations(df: pd.DataFrame, df_budgets: pd.DataFrame) -> dict:
    """
    Analyzes spending patterns and generates personalized savings tips.
    """
    if df.empty:
        return {"recommendations": [], "potential_savings": 0}

    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()
    month_start = now.replace(day=1)

    expenses = df[(df["type"] == "expense") & (df["date"] >= month_start)]
    income_total = df[(df["type"] == "income") & (df["date"] >= month_start)]["amount"].sum()
    expense_total = expenses["amount"].sum()

    category_spend = expenses.groupby("category")["amount"].sum().to_dict()

    recommendations = []
    potential_savings = 0

    # Rule 1: Over-budget categories
    if not df_budgets.empty:
        for _, row in df_budgets.iterrows():
            spent = category_spend.get(row["category"], 0)
            if spent > row["monthly_limit"]:
                over = spent - row["monthly_limit"]
                potential_savings += over * 0.5
                recommendations.append({
                    "type": "budget_alert",
                    "priority": "high",
                    "icon": "⚠️",
                    "title": f"Over Budget: {row['category']}",
                    "detail": f"You've spent ₹{spent:,.0f} vs ₹{row['monthly_limit']:,.0f} budget. "
                              f"Cut by ₹{over:,.0f} to stay within limit.",
                    "saving": round(over * 0.5, 2)
                })

    # Rule 2: 50-30-20 rule analysis
    if income_total > 0:
        needs_pct = expense_total / income_total * 100
        savings_pct = (income_total - expense_total) / income_total * 100

        if savings_pct < 20:
            deficit = (income_total * 0.2) - (income_total - expense_total)
            potential_savings += deficit
            recommendations.append({
                "type": "savings_goal",
                "priority": "high",
                "icon": "🎯",
                "title": "Increase Savings Rate",
                "detail": f"You're saving {savings_pct:.1f}% of income. The 50-30-20 rule recommends "
                          f"saving 20%. Try to save ₹{deficit:,.0f} more this month.",
                "saving": round(deficit, 2)
            })

    # Rule 3: High entertainment / dining spend
    entertainment = category_spend.get("Entertainment", 0)
    food = category_spend.get("Food & Dining", 0)

    if entertainment > 2000:
        save_amt = entertainment * 0.3
        potential_savings += save_amt
        recommendations.append({
            "type": "category_tip",
            "priority": "medium",
            "icon": "🎬",
            "title": "Reduce Entertainment Spend",
            "detail": f"Entertainment at ₹{entertainment:,.0f}/month is high. "
                      f"Share subscriptions or use free alternatives to save ₹{save_amt:,.0f}.",
            "saving": round(save_amt, 2)
        })

    if food > 6000:
        save_amt = food * 0.25
        potential_savings += save_amt
        recommendations.append({
            "type": "category_tip",
            "priority": "medium",
            "icon": "🍽️",
            "title": "Optimize Food Spending",
            "detail": f"Food & Dining at ₹{food:,.0f}/month is above average. "
                      f"Cook at home 3x/week to save ₹{save_amt:,.0f}.",
            "saving": round(save_amt, 2)
        })

    # Rule 4: Emergency fund
    if income_total > 0:
        emergency_target = income_total * 6
        recommendations.append({
            "type": "financial_tip",
            "priority": "low",
            "icon": "🏦",
            "title": "Build Emergency Fund",
            "detail": f"Aim for 6 months of expenses (≈₹{expense_total * 6:,.0f}) as an emergency fund. "
                      f"Start by setting aside ₹{income_total * 0.05:,.0f}/month.",
            "saving": 0
        })

    # Rule 5: Investment tip
    recommendations.append({
        "type": "investment",
        "priority": "low",
        "icon": "📈",
        "title": "Start SIP Investment",
        "detail": "Even ₹500/month in a mutual fund SIP at 12% annual return "
                  "grows to ₹1.12 Lakhs in 10 years through compounding.",
        "saving": 0
    })

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order[x["priority"]])

    return {
        "recommendations": recommendations,
        "potential_savings": round(potential_savings, 2),
        "savings_rate": round((income_total - expense_total) / income_total * 100, 1) if income_total > 0 else 0
    }


# ─── 4. Spending Insights (Anomaly Detection + Pattern Analysis) ───────────────

def get_spending_insights(df: pd.DataFrame) -> dict:
    """
    Generates AI-powered insights: anomalies, top categories, spending patterns.
    """
    if df.empty:
        return {"insights": [], "anomalies": []}

    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.to_period("M")

    expenses = df[df["type"] == "expense"].copy()
    insights = []
    anomalies = []

    if expenses.empty:
        return {"insights": insights, "anomalies": anomalies}

    # 1. Top spending day of week
    day_spend = expenses.groupby("day_of_week")["amount"].sum()
    top_day = day_spend.idxmax()
    insights.append({
        "icon": "📅",
        "title": "Peak Spending Day",
        "text": f"You spend the most on {top_day}s (₹{day_spend[top_day]:,.0f} total). "
                f"Plan purchases on weekdays to reduce impulse buying."
    })

    # 2. Category dominance
    cat_spend = expenses.groupby("category")["amount"].sum()
    top_cat = cat_spend.idxmax()
    top_pct = cat_spend[top_cat] / cat_spend.sum() * 100
    insights.append({
        "icon": "🏆",
        "title": "Dominant Category",
        "text": f"{top_cat} accounts for {top_pct:.1f}% of your total spending. "
                f"Review if this aligns with your priorities."
    })

    # 3. Month-over-month change
    months = sorted(expenses["month"].unique())
    if len(months) >= 2:
        last_m = expenses[expenses["month"] == months[-1]]["amount"].sum()
        prev_m = expenses[expenses["month"] == months[-2]]["amount"].sum()
        change_pct = (last_m - prev_m) / prev_m * 100 if prev_m > 0 else 0
        emoji = "📈" if change_pct > 0 else "📉"
        direction = "increased" if change_pct > 0 else "decreased"
        insights.append({
            "icon": emoji,
            "title": "Month-over-Month Trend",
            "text": f"Spending {direction} by {abs(change_pct):.1f}% compared to last month "
                    f"(₹{last_m:,.0f} vs ₹{prev_m:,.0f})."
        })

    # 4. Anomaly detection (Z-score method)
    cat_stats = expenses.groupby("category")["amount"].agg(["mean", "std"])
    for _, row in expenses.iterrows():
        cat = row.get("category", "Other")
        if cat in cat_stats.index:
            mean = cat_stats.loc[cat, "mean"]
            std = cat_stats.loc[cat, "std"]
            if std > 0:
                z = abs((row["amount"] - mean) / std)
                if z > 2.5:
                    anomalies.append({
                        "date": str(row["date"].date()),
                        "description": row["description"],
                        "amount": row["amount"],
                        "category": cat,
                        "reason": f"Unusually high for {cat} (avg ₹{mean:.0f})"
                    })

    # 5. Savings consistency
    monthly_savings = []
    for m in months[-3:]:
        m_df = df[df["month"] == m]
        inc = m_df[m_df["type"] == "income"]["amount"].sum()
        exp = m_df[m_df["type"] == "expense"]["amount"].sum()
        monthly_savings.append(inc - exp)

    if monthly_savings:
        avg_saving = np.mean(monthly_savings)
        emoji = "✅" if avg_saving > 0 else "❌"
        insights.append({
            "icon": emoji,
            "title": "Savings Consistency",
            "text": f"Average monthly savings over last 3 months: ₹{avg_saving:,.0f}. "
                    + ("Great job maintaining positive savings!" if avg_saving > 0
                       else "Consider reducing expenses to start saving.")
        })

    return {
        "insights": insights,
        "anomalies": anomalies[:5]  # Top 5 anomalies
    }


# ─── 5. AI Finance Chatbot ─────────────────────────────────────────────────────

# def chat_with_ai(message: str, df: pd.DataFrame) -> str:
#     """Rule-based AI chatbot with financial context awareness."""
#     msg = message.lower().strip()
    
#     # Build financial context
#     if not df.empty:
#         df["date"] = pd.to_datetime(df["date"])
#         now = datetime.now()
#         month_start = now.replace(day=1)
        
#         # Get this month's transactions
#         monthly_exp = df[(df["type"] == "expense") & (df["date"] >= month_start)]["amount"]
#         monthly_inc = df[(df["type"] == "income") & (df["date"] >= month_start)]["amount"]
        
#         total_expense = monthly_exp.sum()
#         total_income = monthly_inc.sum()
#         savings = total_income - total_expense
#         savings_rate = (savings / total_income * 100) if total_income > 0 else 0
        
#         # Get category spending
#         cat_spend = df[(df["type"] == "expense") & (df["date"] >= month_start)]\
#             .groupby("category")["amount"].sum().sort_values(ascending=False)
#         top_category = cat_spend.index[0] if not cat_spend.empty else "N/A"
#         top_amount = cat_spend.iloc[0] if not cat_spend.empty else 0
        
#         # Get total transactions count
#         total_txns = len(df)
        
#     else:
#         total_expense = total_income = savings = savings_rate = 0
#         top_category = "N/A"
#         top_amount = 0
#         total_txns = 0
    
#     # ── Intent matching ──
    
#     # Spending summary
#     if any(w in msg for w in ["spend", "spent", "expense", "how much", "total"]):
#         if "category" in msg or any(cat.lower() in msg for cat in cat_spend.index if not df.empty):
#             for cat in (cat_spend.index if not df.empty else []):
#                 if cat.lower() in msg:
#                     return f"You've spent ₹{cat_spend[cat]:,.0f} on {cat} this month. That's {cat_spend[cat]/total_expense*100:.1f}% of your total expenses."
#         return f"This month you've spent ₹{total_expense:,.2f} in total. Your highest spending category is {top_category} at ₹{top_amount:,.0f}."
    
#     # Savings queries
#     elif any(w in msg for w in ["sav", "saving", "save money"]):
#         if savings > 0:
#             return f"You've saved ₹{savings:,.2f} this month — a {savings_rate:.1f}% savings rate. The recommended rate is 20%. " + ("You're doing great! 🎉" if savings_rate >= 20 else f"Try to increase savings by ₹{(total_income*0.2-savings):,.0f} more.")
#         else:
#             return f"This month you're overspending by ₹{abs(savings):,.0f}. Cut discretionary spending in {top_category} to get back on track."
    
#     # Income queries
#     elif any(w in msg for w in ["income", "earn", "salary"]):
#         return f"Your total income this month is ₹{total_income:,.2f}."
    
#     # Budget advice
#     elif any(w in msg for w in ["budget", "plan", "allocat"]):
#         needs = total_income * 0.50
#         wants = total_income * 0.30
#         savings_goal = total_income * 0.20
#         return f"Based on your income of ₹{total_income:,.0f}, the 50-30-20 budget rule suggests:\n• Needs (rent, food, utilities): ₹{needs:,.0f}\n• Wants (entertainment, shopping): ₹{wants:,.0f}\n• Savings & investments: ₹{savings_goal:,.0f}"
    
#     # Investment advice
#     elif any(w in msg for w in ["invest", "mutual fund", "sip", "stock", "fd"]):
#         return "Here are some investment options for beginners:\n• SIP in Mutual Funds: Start from ₹500/month (ELSS for tax saving)\n• PPF: Safe long-term investment with tax benefits (15-year lock-in)\n• Fixed Deposits: 6-7% interest, ideal for emergency fund\n• Index Funds: Low-cost, market-tracking investments\n• NPS: National Pension System for retirement planning\n\n⚠️ This is general info, not financial advice. Consult a SEBI-registered advisor."
    
#     # EMI / loan
#     elif any(w in msg for w in ["emi", "loan", "debt", "credit"]):
#         return f"Managing debt effectively:\n• Keep EMIs under 40% of monthly income\n• Always pay credit card bill in full to avoid 36-48% interest\n• Use the avalanche method: pay highest interest debt first\n• Avoid taking loans for depreciating assets like gadgets\n• With your income of ₹{total_income:,.0f}, max safe EMI is ₹{total_income*0.4:,.0f}"
    
#     # Tax
#     elif any(w in msg for w in ["tax", "itr", "deduction"]):
#         return "Tax-saving tips (India):\n• Section 80C: Save up to ₹1.5L via ELSS, PPF, LIC, ULIP, home loan principal\n• Section 80D: Health insurance premium deduction up to ₹25,000\n• HRA exemption: If paying rent, claim HRA\n• Section 80CCC: NPS contribution up to ₹50,000 extra\n• File ITR by July 31 every year to avoid penalties"
    
#     # Emergency fund
#     elif any(w in msg for w in ["emergency", "fund", "backup"]):
#         target = total_expense * 6
#         return f"Emergency fund target: 6 months of expenses = ₹{target:,.0f}. Keep this in a high-yield savings account or liquid mutual fund. Start by saving 5% of income (₹{total_income*0.05:,.0f}/month) until you reach the target."
    
#     # Greeting
#     elif any(w in msg for w in ["hello", "hi", "hey", "namaste", "hii"]):
#         return f"Hello! 👋 I'm your FinTrack AI assistant.\n\n📊 Your current financial snapshot:\n💰 Income: ₹{total_income:,.0f}\n💸 Expenses: ₹{total_expense:,.0f}\n🏦 Savings: ₹{savings:,.0f} ({savings_rate:.1f}%)\n📝 Total Transactions: {total_txns}\n\nI can help you with:\n• Spending summaries and analysis\n• Savings tips and recommendations\n• Budget planning (50-30-20 rule)\n• Investment advice\n• Tax-saving strategies\n\nWhat would you like to know about your finances?"
    
#     # Help
#     elif any(w in msg for w in ["help", "what can", "feature"]):
#         return "I can answer questions like:\n• 'How much did I spend this month?'\n• 'What are my savings?'\n• 'Give me budget advice'\n• 'How should I invest my money?'\n• 'How can I save on taxes?'\n• 'What is my top spending category?'\n• 'How do I build an emergency fund?'"
    
#     # Top spending category
#     elif any(w in msg for w in ["top", "highest", "most", "biggest"]):
#         return f"Your highest spending category this month is {top_category} at ₹{top_amount:,.0f} ({top_amount/total_expense*100:.1f}% of expenses)."
    
#     # Transactions count
#     elif any(w in msg for w in ["transaction", "entries", "records"]):
#         return f"You have {total_txns} total transactions in your database. This month you've made {len(df[df['date'] >= month_start])} transactions."
    
#     # Default
#     else:
#         return f"Here's your financial snapshot:\n💰 Income: ₹{total_income:,.0f}\n💸 Expenses: ₹{total_expense:,.0f}\n🏦 Savings: ₹{savings:,.0f} ({savings_rate:.1f}%)\n📝 Total Transactions: {total_txns}\n\nTry asking: 'How much did I spend?', 'Give me savings tips', or 'Budget advice'."

def chat_with_ai(message: str, df: pd.DataFrame) -> str:
    """AI Chatbot - Returns a generic response for all messages"""
    return "🚀 This feature is coming soon! We're working hard to bring you an amazing AI assistant. Stay tuned! 🎉"