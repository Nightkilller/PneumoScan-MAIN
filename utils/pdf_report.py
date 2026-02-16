"""
PneumoScan – Professional PDF Diagnostic Report Generator
Uses ReportLab + Matplotlib to produce a hospital-style report.
"""

import os
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Color palette ────────────────────────────────────────────────────────
PRIMARY   = HexColor("#1a237e")
ACCENT    = HexColor("#0d47a1")
GREEN     = HexColor("#2e7d32")
RED       = HexColor("#c62828")
LIGHT_BG  = HexColor("#e8eaf6")
WHITE     = HexColor("#ffffff")
GRAY      = HexColor("#616161")
DARK      = HexColor("#212121")


def _build_chart(pneumonia_prob: float, normal_prob: float) -> str:
    """Return path to a temporary bar-chart PNG."""
    fig, ax = plt.subplots(figsize=(4.5, 2.2))
    labels = ["Normal", "Pneumonia"]
    values = [normal_prob, pneumonia_prob]
    colors = ["#43a047", "#e53935"]
    bars = ax.barh(labels, values, color=colors, height=0.55, edgecolor="white", linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 1.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=10, fontweight="bold", color="#333")

    ax.set_xlim(0, 110)
    ax.set_xlabel("Probability (%)", fontsize=9, color="#555")
    ax.tick_params(axis="y", labelsize=11)
    ax.tick_params(axis="x", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_report(
    output_path: str,
    patient_name: str,
    patient_age: str,
    notes: str,
    prediction: str,
    confidence: float,
    pneumonia_prob: float,
    normal_prob: float,
    image_path: str | None = None,
):
    """Generate a professional diagnostic PDF report."""

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=PRIMARY,
        spaceAfter=2 * mm,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=ACCENT,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK,
        leading=15,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GRAY,
        alignment=TA_CENTER,
    )

    elements = []

    # ── Header ───────────────────────────────────────────────────────────
    elements.append(Paragraph("🫁 PneumoScan", title_style))
    elements.append(Paragraph("AI Diagnostic Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=PRIMARY, spaceAfter=4 * mm))

    # ── Date/Time ────────────────────────────────────────────────────────
    now = datetime.now().strftime("%B %d, %Y  •  %I:%M %p")
    elements.append(Paragraph(f"<b>Date &amp; Time:</b>  {now}", body_style))
    elements.append(Spacer(1, 3 * mm))

    # ── Patient Info ─────────────────────────────────────────────────────
    elements.append(Paragraph("Patient Information", section_style))
    info_data = [
        ["Patient Name", patient_name or "N/A"],
        ["Age", str(patient_age) if patient_age else "N/A"],
        ["Notes", notes or "—"],
    ]
    info_table = Table(info_data, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdbdbd")),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [WHITE, HexColor("#f5f5f5")]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Analysis Result ──────────────────────────────────────────────────
    elements.append(Paragraph("Analysis Result", section_style))

    result_color = RED if prediction == "PNEUMONIA" else GREEN
    result_label = prediction
    result_conf = f"{confidence}%"

    result_data = [
        ["Prediction", result_label],
        ["Confidence", result_conf],
    ]
    result_table = Table(result_data, colWidths=[45 * mm, 120 * mm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("TEXTCOLOR", (1, 0), (1, 0), result_color),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdbdbd")),
    ]))
    elements.append(result_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Confidence Chart ─────────────────────────────────────────────────
    elements.append(Paragraph("Confidence Chart", section_style))
    chart_buf = _build_chart(pneumonia_prob, normal_prob)
    chart_img = RLImage(chart_buf, width=140 * mm, height=62 * mm)
    elements.append(chart_img)
    elements.append(Spacer(1, 5 * mm))

    # ── X-ray Image ──────────────────────────────────────────────────────
    if image_path and os.path.exists(image_path):
        elements.append(Paragraph("Uploaded X-ray", section_style))
        try:
            xray = RLImage(image_path, width=90 * mm, height=90 * mm, kind="proportional")
            elements.append(xray)
        except Exception:
            elements.append(Paragraph("<i>Unable to embed image.</i>", body_style))
        elements.append(Spacer(1, 6 * mm))

    # ── Footer ───────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.8, color=GRAY, spaceBefore=6 * mm, spaceAfter=3 * mm))
    elements.append(Paragraph("Made with ❤️ by Aditya", footer_style))
    elements.append(Paragraph("This report is generated by PneumoScan AI and is for informational purposes only.", footer_style))

    doc.build(elements)
