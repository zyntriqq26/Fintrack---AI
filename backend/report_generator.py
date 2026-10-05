"""
FinTrack AI - Monthly Report Generator
Generates a professional PDF financial report using ReportLab.
Multi-user aware: PDFs are namespaced by user_id to prevent collisions
and data leaks between users.
"""

import os
from datetime import datetime
import pandas as pd

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, \
                                    Paragraph, Spacer, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════
def generate_monthly_report(df: pd.DataFrame,
                             df_budgets: pd.DataFrame,
                             month: str,
                             user_id: int) -> str:
    """
    Generate a monthly financial report PDF for a specific user.

    Args:
        df          : transactions DataFrame (already filtered to this user)
        df_budgets  : budgets DataFrame     (already filtered to this user)
        month       : 'YYYY-MM' string
        user_id     : integer user ID (used to namespace the output file)

    Returns:
        Path to the generated file (PDF, or TXT fallback if ReportLab is absent).
    """
    os.makedirs("reports", exist_ok=True)

    # ── Namespace the filename by user_id ────────────────────────
    # The 'user<id>_' prefix is what auth-protected /reports and
    # /reports/<filename> endpoints check for ownership.
    base_name = f"user{user_id}_FinTrack_Report_{month}"
    path = f"reports/{base_name}.pdf"

    if not REPORTLAB_AVAILABLE:
        path = path.replace(".pdf", ".txt")
        _generate_text_report(df, df_budgets, month, path)
        return path

    # ── Filter for the requested month ───────────────────────────
    if df.empty:
        # Generate a "no data" PDF anyway so the user doesn't see a crash
        return _generate_empty_report(path, month)

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    year, mon = map(int, month.split("-"))
    mask = (df["date"].dt.year == year) & (df["date"].dt.month == mon)
    month_df = df[mask]

    income_total = float(month_df[month_df["type"] == "income"]["amount"].sum() or 0)
    expense_total = float(month_df[month_df["type"] == "expense"]["amount"].sum() or 0)
    savings = income_total - expense_total
    savings_rate = (savings / income_total * 100) if income_total > 0 else 0

    cat_spend = month_df[month_df["type"] == "expense"] \
                        .groupby("category")["amount"].sum()

    # ── Build PDF ────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    story = []

    # Palette
    PRIMARY   = colors.HexColor("#6366F1")
    SECONDARY = colors.HexColor("#10B981")
    DANGER    = colors.HexColor("#EF4444")
    DARK      = colors.HexColor("#1E293B")
    LIGHT_BG  = colors.HexColor("#F8FAFC")
    INCOME_BLUE = colors.HexColor("#1e00c7")

    # Header
    header_style = ParagraphStyle(
        "Header", fontSize=28, textColor=PRIMARY,
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "Sub", fontSize=12, textColor=DARK,
        spaceAfter=2, alignment=TA_CENTER, fontName="Helvetica",
    )

    story.append(Spacer(1, 20))
    story.append(Paragraph("FinTrack AI", header_style))
    story.append(Spacer(1, 12))
    month_name = datetime(year, mon, 1).strftime("%B %Y")
    story.append(Paragraph(f"Monthly Financial Report — {month_name}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=PRIMARY, spaceAfter=20))

    section_style = ParagraphStyle(
        "Section", fontSize=14, textColor=PRIMARY,
        spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold",
    )

    # ── Financial Summary ────────────────────────────────────────
    story.append(Paragraph("Financial Summary", section_style))

    summary_data = [
        ["Metric",            "Amount",                "Status"],
        ["Total Income",      f"{income_total:,.2f}",  "✓"],
        ["Total Expenses",    f"{expense_total:,.2f}", "✓"],
        ["Net Savings",       f"{savings:,.2f}",       "✓" if savings >= 0 else "✗"],
        ["Savings Rate",      f"{savings_rate:.1f}%",
         "✓" if savings_rate >= 20 else "↑ Improve"],
    ]

    t = Table(summary_data, colWidths=[8*cm, 6*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 11),
        ("BACKGROUND",    (0, 1), (-1, -1), LIGHT_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",       (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",     (1, 1), (1, 1), INCOME_BLUE),
        ("TEXTCOLOR",     (1, 2), (1, 2), DANGER),
        ("TEXTCOLOR",     (1, 3), (1, 3),
         SECONDARY if savings >= 0 else DANGER),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Category Breakdown ───────────────────────────────────────
    story.append(Paragraph("Spending by Category", section_style))

    if not cat_spend.empty:
        cat_data = [["Category", "Amount (INR)", "% of Expenses"]]
        for cat, amt in cat_spend.sort_values(ascending=False).items():
            pct = (amt / expense_total * 100) if expense_total > 0 else 0
            cat_data.append([cat, f"{amt:,.2f}", f"{pct:.1f}%"])

        ct = Table(cat_data, colWidths=[8*cm, 6*cm, 4*cm])
        ct.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
            ("PADDING",       (0, 0), (-1, -1), 7),
        ]))
        story.append(ct)
    else:
        story.append(Paragraph("No expenses recorded for this month.",
                                sub_style))

    story.append(Spacer(1, 16))

    # ── Budget vs Actual ─────────────────────────────────────────
    if df_budgets is not None and not df_budgets.empty:
        story.append(Paragraph("Budget vs Actual", section_style))
        bud_data = [["Category", "Budget (INR)", "Actual (INR)", "Status"]]
        for _, row in df_budgets.iterrows():
            actual = cat_spend.get(row["category"], 0)
            status = "✓ Under" if actual <= row["monthly_limit"] else "✗ Over"
            bud_data.append([
                row["category"],
                f"{row['monthly_limit']:,.0f}",
                f"{actual:,.0f}",
                status,
            ])

        bt = Table(bud_data, colWidths=[6*cm, 4*cm, 4*cm, 4*cm])
        bt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 10),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
            ("PADDING",       (0, 0), (-1, -1), 7),
        ]))
        story.append(bt)

    # ── Top Transactions ─────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(Paragraph("Top Transactions This Month", section_style))

    top_txns = month_df[month_df["type"] == "expense"].nlargest(10, "amount")
    if not top_txns.empty:
        txn_data = [["Date", "Description", "Category", "Amount (INR)"]]
        for _, row in top_txns.iterrows():
            txn_data.append([
                str(row["date"].date()),
                str(row["description"])[:30],
                row.get("category", "Other"),
                f"{row['amount']:,.2f}",
            ])

        tt = Table(txn_data, colWidths=[4*cm, 7*cm, 5*cm, 4*cm])
        tt.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN",         (3, 0), (3, -1), "RIGHT"),
            ("PADDING",       (0, 0), (-1, -1), 6),
        ]))
        story.append(tt)
    else:
        story.append(Paragraph("No transactions recorded for this month.",
                                sub_style))

    # ── Footer ───────────────────────────────────────────────────
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1,
                            color=colors.HexColor("#E2E8F0")))
    footer_style = ParagraphStyle(
        "Footer", fontSize=8, textColor=colors.grey,
        alignment=TA_CENTER, spaceBefore=8,
    )
    story.append(Paragraph(
        f"Generated by FinTrack AI | "
        f"{datetime.now().strftime('%d %b %Y, %H:%M')} | "
        f"User ID: {user_id} | For personal use only",
        footer_style,
    ))

    doc.build(story)
    return path


# ═══════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════
def _generate_empty_report(path: str, month: str) -> str:
    """Generate a small 'no data' PDF so the user gets a friendly file."""
    doc = SimpleDocTemplate(path, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    title_style = ParagraphStyle(
        "T", fontSize=24, textColor=colors.HexColor("#6366F1"),
        alignment=TA_CENTER, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "B", fontSize=12, textColor=colors.HexColor("#1E293B"),
        alignment=TA_CENTER, spaceBefore=20,
    )
    story.append(Spacer(1, 60))
    story.append(Paragraph("FinTrack AI", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"No transactions recorded for "
        f"{datetime.strptime(month, '%Y-%m').strftime('%B %Y')}.",
        body_style,
    ))
    doc.build(story)
    return path


def _generate_text_report(df, df_budgets, month, path):
    """Fallback text report if ReportLab is not installed."""
    if df.empty:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"FinTrack AI - Monthly Financial Report\n{month}\n"
                    f"No transactions recorded.\n")
        return

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    year, mon = map(int, month.split("-"))
    mask = (df["date"].dt.year == year) & (df["date"].dt.month == mon)
    month_df = df[mask]

    income = month_df[month_df["type"] == "income"]["amount"].sum()
    expenses = month_df[month_df["type"] == "expense"]["amount"].sum()
    savings = income - expenses
    rate = (savings / income * 100) if income > 0 else 0

    lines = [
        "=" * 50,
        "  FinTrack AI - Monthly Financial Report",
        f"  {datetime(year, mon, 1).strftime('%B %Y')}",
        "=" * 50,
        f"\nTotal Income:   Rs {income:,.2f}",
        f"Total Expenses: Rs {expenses:,.2f}",
        f"Net Savings:    Rs {savings:,.2f}",
        f"Savings Rate:   {rate:.1f}%\n",
        "\nSpending by Category:",
        "-" * 30,
    ]

    cat_spend = month_df[month_df["type"] == "expense"] \
                        .groupby("category")["amount"].sum()
    for cat, amt in cat_spend.sort_values(ascending=False).items():
        lines.append(f"  {cat:<20} Rs {amt:>10,.2f}")

    lines += ["\n" + "=" * 50, "Generated by FinTrack AI"]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))