"""
FinTrack AI - Monthly Report Generator
Generates a professional PDF financial report using ReportLab.
"""

import os
from datetime import datetime
import pandas as pd

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_monthly_report(df: pd.DataFrame, df_budgets: pd.DataFrame, month: str) -> str:
    """
    Generate a monthly financial report PDF.
    Falls back to a plain text file if ReportLab is not installed.
    """
    os.makedirs("reports", exist_ok=True)
    path = f"reports/FinTrack_Report_{month}.pdf"

    if not REPORTLAB_AVAILABLE:
        path = path.replace(".pdf", ".txt")
        _generate_text_report(df, df_budgets, month, path)
        return path

    # Filter for requested month
    df["date"] = pd.to_datetime(df["date"])
    year, mon = map(int, month.split("-"))
    mask = (df["date"].dt.year == year) & (df["date"].dt.month == mon)
    month_df = df[mask]

    income_total = month_df[month_df["type"] == "income"]["amount"].sum()
    expense_total = month_df[month_df["type"] == "expense"]["amount"].sum()
    savings = income_total - expense_total
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0

    cat_spend = month_df[month_df["type"] == "expense"].groupby("category")["amount"].sum()

    # ── Build PDF ──
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Color palette
    PRIMARY = colors.HexColor("#6366F1")
    SECONDARY = colors.HexColor("#10B981")
    DANGER = colors.HexColor("#EF4444")
    DARK = colors.HexColor("#1E293B")
    LIGHT_BG = colors.HexColor("#F8FAFC")
    NEEELA=colors.HexColor("#1e00c7")

    # Header
    header_style = ParagraphStyle("Header", fontSize=28, textColor=PRIMARY,
                                  spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold")
    sub_style = ParagraphStyle("Sub", fontSize=12, textColor=DARK,
                               spaceAfter=2, alignment=TA_CENTER, fontName="Helvetica")

    story.append(Spacer(1,20))
    story.append(Paragraph("FinTrack AI", header_style))
    story.append(Spacer(1,12))
    month_name = datetime(year, mon, 1).strftime("%B %Y")
    story.append(Paragraph(f"Monthly Financial Report — {month_name}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=20))

    # Summary Cards Table
    section_style = ParagraphStyle("Section", fontSize=14, textColor=PRIMARY,
                                   spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold")
    story.append(Paragraph("Financial Summary", section_style))

    summary_data = [
        ["Metric", "Amount", "Status"],
        ["Total Income", f"{income_total:,.2f}", "✓"],
        ["Total Expenses", f"{expense_total:,.2f}", "✓"],
        ["Net Savings", f"{savings:,.2f}", "✓" if savings >= 0 else "✗"],
        ["Savings Rate", f"{savings_rate:.1f}%", "✓" if savings_rate >= 20 else "↑ Improve"],
    ]

    t = Table(summary_data, colWidths=[8*cm, 6*cm, 4*cm])
    t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 11),
    ("BACKGROUND", (0, 1), (-1, -1), LIGHT_BG),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 1), (-1, -1), 10),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("PADDING", (0, 0), (-1, -1), 8),
    # Color Income row (row index 1) green
    ("TEXTCOLOR", (1, 1), (1, 1), NEEELA),
    # Color Expenses row (row index 2) red
    ("TEXTCOLOR", (1, 2), (1, 2), DANGER),
    # Color Savings row based on value (row index 3)
    ("TEXTCOLOR", (1, 3), (1, 3), SECONDARY if savings >= 0 else DANGER),
]))
    story.append(t)
    story.append(Spacer(1, 16))

    # Category Breakdown
    story.append(Paragraph("Spending by Category", section_style))

    if not cat_spend.empty:
        cat_data = [["Category", "Amount (INR)", "% of Expenses"]]
        for cat, amt in cat_spend.sort_values(ascending=False).items():
            pct = (amt / expense_total * 100) if expense_total > 0 else 0
            cat_data.append([cat, f"{amt:,.2f}", f"{pct:.1f}%"])

        ct = Table(cat_data, colWidths=[8*cm, 6*cm, 4*cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366F1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(ct)

    story.append(Spacer(1, 16))

    # Budget vs Actual
    if not df_budgets.empty:
        story.append(Paragraph("Budget vs Actual", section_style))
        bud_data = [["Category", "Budget (INR)", "Actual (INR)", "Status"]]
        for _, row in df_budgets.iterrows():
            actual = cat_spend.get(row["category"], 0)
            status = "✓ Under" if actual <= row["monthly_limit"] else "✗ Over"
            bud_data.append([row["category"], f"{row['monthly_limit']:,.0f}",
                             f"{actual:,.0f}", status])

        bt = Table(bud_data, colWidths=[6*cm, 4*cm, 4*cm, 4*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(bt)

    # Recent Transactions
    story.append(Spacer(1, 16))
    story.append(Paragraph("Top Transactions This Month", section_style))
    top_txns = month_df[month_df["type"] == "expense"].nlargest(10, "amount")
    if not top_txns.empty:
        txn_data = [["Date", "Description", "Category", "Amount (INR)"]]
        for _, row in top_txns.iterrows():
            txn_data.append([
                str(row["date"].date()),
                row["description"][:30],
                row.get("category", "Other"),
                f"{row['amount']:,.2f}"
            ])
        tt = Table(txn_data, colWidths=[4*cm, 7*cm, 5*cm, 4*cm])
        tt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tt)

    # Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
    footer_style = ParagraphStyle("Footer", fontSize=8, textColor=colors.grey,
                                  alignment=TA_CENTER, spaceBefore=8)
    story.append(Paragraph(
        f"Generated by FinTrack AI | {datetime.now().strftime('%d %b %Y, %H:%M')} | For personal use only",
        footer_style
    ))

    doc.build(story)
    return path


def _generate_text_report(df, df_budgets, month, path):
    """Fallback text report if ReportLab not installed."""
    df["date"] = pd.to_datetime(df["date"])
    year, mon = map(int, month.split("-"))
    mask = (df["date"].dt.year == year) & (df["date"].dt.month == mon)
    month_df = df[mask]

    income = month_df[month_df["type"] == "income"]["amount"].sum()
    expenses = month_df[month_df["type"] == "expense"]["amount"].sum()
    savings = income - expenses

    lines = [
        "=" * 50,
        "  FinTrack AI - Monthly Financial Report",
        f"  {datetime(year, mon, 1).strftime('%B %Y')}",
        "=" * 50,
        f"\nTotal Income:   ₹{income:,.2f}",
        f"Total Expenses: ₹{expenses:,.2f}",
        f"Net Savings:    ₹{savings:,.2f}",
        f"Savings Rate:   {(savings/income*100):.1f}%\n",
        "\nSpending by Category:",
        "-" * 30,
    ]

    cat_spend = month_df[month_df["type"] == "expense"].groupby("category")["amount"].sum()
    for cat, amt in cat_spend.sort_values(ascending=False).items():
        lines.append(f"  {cat:<20} ₹{amt:>10,.2f}")

    lines += ["\n" + "=" * 50, "Generated by FinTrack AI"]

    with open(path, "w") as f:
        f.write("\n".join(lines))