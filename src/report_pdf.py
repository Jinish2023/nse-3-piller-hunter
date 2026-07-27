"""
Colour-coded PDF report — pure technical, no macro news, no AI narrative.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle

PDF_PAGE_W, PDF_PAGE_H = A4
PDF_MARGIN_L = 18 * mm
PDF_MARGIN_R = 18 * mm
PDF_MARGIN_TOP = 20 * mm
PDF_MARGIN_BOTTOM = 16 * mm

CARD_ACCENT = HexColor("#4F46E5")   # single fixed accent — no news-driven theme colors
CARD_BG = HexColor("#EEF2FF")
LEVELS_BG = HexColor("#F5F7FF")


def _pdf_styles():
    return {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=HexColor("#0F172A")),
        "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=10, leading=13, textColor=HexColor("#64748B")),
        "disclaimer": ParagraphStyle("Disclaimer", fontName="Helvetica-Oblique", fontSize=8.3, leading=12, textColor=HexColor("#7C2D12")),
        "card_symbol": ParagraphStyle("CardSymbol", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=white),
        "card_sub": ParagraphStyle("CardSub", fontName="Helvetica", fontSize=8, leading=11, textColor=white),
        "levels": ParagraphStyle("Levels", fontName="Helvetica", fontSize=9, leading=13, textColor=HexColor("#1E293B")),
        "levels_bold": ParagraphStyle("LevelsBold", fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=HexColor("#0F172A")),
        "tags": ParagraphStyle("Tags", fontName="Helvetica", fontSize=8.4, leading=12.5, textColor=HexColor("#475569")),
        "rationale": ParagraphStyle("Rationale", fontName="Helvetica", fontSize=9, leading=13.5, textColor=HexColor("#1E293B"), spaceBefore=3),
    }


def _fmt_vol(v):
    """Formats a share count in Indian units (Lakh/Crore) for readability."""
    if v >= 1_00_00_000:
        return f"{v / 1_00_00_000:.2f}Cr"
    if v >= 1_00_000:
        return f"{v / 1_00_000:.2f}L"
    if v >= 1_000:
        return f"{v / 1_000:.1f}K"
    return f"{v:.0f}"


def _stock_card(candidate, styles):
    lv = candidate["levels"]

    header = Table(
        [[Paragraph(candidate["symbol"], styles["card_symbol"]),
          Paragraph("3-PILLAR MOMENTUM SETUP", styles["card_sub"])]],
        colWidths=[(PDF_PAGE_W - PDF_MARGIN_L - PDF_MARGIN_R) * 0.6,
                   (PDF_PAGE_W - PDF_MARGIN_L - PDF_MARGIN_R) * 0.4],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_ACCENT),
        ("LEFTPADDING", (0, 0), (0, 0), 10),
        ("RIGHTPADDING", (1, 0), (1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))

    vol_today_fmt = _fmt_vol(candidate["volume_today"])
    vol_avg_fmt = _fmt_vol(candidate["volume_avg20"])

    levels_data = [
        [Paragraph("CMP", styles["levels"]), Paragraph(f"Rs. {candidate['close']:.1f}", styles["levels_bold"]),
         Paragraph("RSI(14)", styles["levels"]), Paragraph(f"{candidate['rsi']:.0f}", styles["levels_bold"])],
        [Paragraph("Entry Zone", styles["levels"]), Paragraph(f"Rs. {lv['entry_low']}\u2013{lv['entry_high']}", styles["levels_bold"]),
         Paragraph("Volume (today / 20d avg)", styles["levels"]),
         Paragraph(f"{vol_today_fmt} / {vol_avg_fmt} ({candidate['vol_surge']:.1f}x)", styles["levels_bold"])],
        [Paragraph("Stop Loss", styles["levels"]), Paragraph(f"Rs. {lv['stop_loss']} ({lv['stop_loss_pct']:+.1f}%)", styles["levels_bold"]),
         Paragraph("Target 1 / 2", styles["levels"]),
         Paragraph(f"Rs. {lv['target1']} ({lv['target1_pct']:+.1f}%) / Rs. {lv['target2']} ({lv['target2_pct']:+.1f}%)", styles["levels_bold"])],
    ]
    levels_table = Table(levels_data, colWidths=[30 * mm, 34 * mm, 38 * mm, 52 * mm])
    levels_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LEVELS_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    tags_text = " &nbsp;•&nbsp; ".join(candidate["tags"])
    tags_para = Paragraph(tags_text, styles["tags"])

    body_rows = [[levels_table], [Spacer(1, 4)], [tags_para]]

    body = Table(body_rows, colWidths=[PDF_PAGE_W - PDF_MARGIN_L - PDF_MARGIN_R])
    body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BOX", (0, 0), (-1, -1), 0.6, HexColor("#E2E8F0")),
    ]))

    return KeepTogether([header, body, Spacer(1, 10)])


def _pdf_footer(run_label):
    def _on_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(HexColor("#E2E8F0"))
        canvas.setLineWidth(0.6)
        canvas.line(PDF_MARGIN_L, PDF_MARGIN_BOTTOM - 6, PDF_PAGE_W - PDF_MARGIN_R, PDF_MARGIN_BOTTOM - 6)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(HexColor("#94A3B8"))
        canvas.drawString(PDF_MARGIN_L, PDF_MARGIN_BOTTOM - 15, f"NSE Momentum Swing Scanner — {run_label} — Not investment advice")
        canvas.drawRightString(PDF_PAGE_W - PDF_MARGIN_R, PDF_MARGIN_BOTTOM - 15, f"Page {doc.page}")
        canvas.restoreState()
    return _on_page


def build_pdf(candidates, run_label, output_path):
    styles = _pdf_styles()
    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=PDF_MARGIN_L, rightMargin=PDF_MARGIN_R,
        topMargin=PDF_MARGIN_TOP, bottomMargin=PDF_MARGIN_BOTTOM + 8,
        title=f"NSE Momentum Swing Scan — {run_label}", author="Automated Momentum Swing Scanner",
    )
    frame = Frame(
        PDF_MARGIN_L, PDF_MARGIN_BOTTOM + 8,
        PDF_PAGE_W - PDF_MARGIN_L - PDF_MARGIN_R,
        PDF_PAGE_H - PDF_MARGIN_TOP - PDF_MARGIN_BOTTOM - 8,
        id="normal",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_pdf_footer(run_label))])

    story = [
        Paragraph("NSE Momentum Swing Scanner — 3-Pillar Daily Screen", styles["title"]),
        Paragraph(run_label, styles["subtitle"]),
        Spacer(1, 8),
        Paragraph(
            "Educational / research tool only — NOT investment advice. Every candidate below cleared "
            "Pillar 1 (Trend: price above EMA200 &amp; a rising daily trendline), Pillar 2 (Momentum: "
            "RSI 40-70 &amp; rising, EMA44 sloping up, price above EMA44, volume participation), and the "
            "volume-confirmation half of Pillar 3 (up day, RVOL above threshold) — all computed on the "
            "DAILY chart from real OHLCV data. Purely technical — no news or AI narrative is used. "
            "Verify independently and consult a SEBI-registered advisor before trading. Past patterns "
            "do not guarantee future moves.",
            styles["disclaimer"],
        ),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1.2, color=HexColor("#0F172A"), spaceAfter=10),
    ]

    if not candidates:
        story.append(Paragraph("No candidates cleared all 3 pillars + liquidity filters today.", styles["rationale"]))
    else:
        for c in candidates:
            story.append(_stock_card(c, styles))

    doc.build(story)
