# 💰 FinTrack AI

> AI-Powered Personal Finance Manager

FinTrack AI is a web application that helps you track your income, expenses, and savings. It uses intelligent analysis to categorise transactions automatically, predict future spending, provide savings recommendations, and generate professional monthly reports.

![FinTrack AI Dashboard](https://via.placeholder.com/800x400?text=FinTrack+AI+Dashboard)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Dashboard** | Real‑time overview of income, expenses, savings, spending by category, and monthly trends. |
| 📝 **Transaction Management** | Add, search, filter, and delete transactions. Automatic AI‑powered categorisation. |
| 💰 **Budget Tracking** | Set monthly spending limits per category and track your progress with visual bars. |
| 📈 **Analytics** | Get deep insights: spending patterns, anomaly detection, and expense predictions. |
| 🤖 **AI Assistant** | Chat with a financial assistant (feature coming soon). |
| 📄 **Monthly Reports** | Generate and download detailed PDF financial reports. |
| 🌙 **Dark Mode** | Toggle between light and dark themes for comfortable viewing. |

---

## 🧠 How It Works

- **Transaction Categorization**: Uses keyword‑based matching to automatically categorise expenses (e.g., "Zomato" → Food & Dining).
- **Expense Prediction**: Linear regression analysis on historical monthly data to forecast future spending by category.
- **Savings Recommendations**: Compares actual spending with budget limits and suggests actionable tips.
- **Spending Insights**: Detects unusual transactions using Z‑score and identifies peak spending days and dominant categories.
- **Chatbot**: Rule‑based intent matching that answers financial queries (currently under development).

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Database | SQLite |
| ML Engine | Pandas, NumPy |
| PDF Reports | ReportLab |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Deployment | PythonAnywhere / Render / Railway (persistent storage recommended) |

---

## 🚀 Installation (Local Development)

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_ORGANIZATION_NAME/fintrack-ai.git
cd fintrack-ai/backend