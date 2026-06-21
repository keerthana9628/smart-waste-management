"""
PDF Report Generator
---------------------
Builds a professional PDF report summarizing waste collection
statistics and bin utilization using ReportLab.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


GREEN = colors.HexColor('#2e7d32')
LIGHT_GREEN = colors.HexColor('#e8f5e9')


def generate_report_pdf(report_title, period_label, summary_stats, bin_rows, collection_rows):
    """Generate a PDF report and return it as a BytesIO buffer.

    Args:
        report_title (str): Title shown at the top of the report.
        period_label (str): e.g. "Daily Report - 2026-06-15"
        summary_stats (dict): key/value pairs shown in a summary table.
        bin_rows (list[list]): table rows for bin utilization
                                (header row included).
        collection_rows (list[list]): table rows for collection history
                                       (header row included).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleGreen', parent=styles['Title'], textColor=GREEN, spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'], textColor=colors.grey, spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'HeadingGreen', parent=styles['Heading2'], textColor=GREEN, spaceBefore=14, spaceAfter=6
    )

    elements = []
    elements.append(Paragraph('🌿 Smart Waste Management System', subtitle_style))
    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph(period_label, subtitle_style))
    elements.append(Paragraph(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', subtitle_style))
    elements.append(Spacer(1, 0.4 * cm))

    # ---- Summary stats table ----
    elements.append(Paragraph('Summary', heading_style))
    summary_table_data = [['Metric', 'Value']] + [[k, str(v)] for k, v in summary_stats.items()]
    summary_table = Table(summary_table_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(_table_style())
    elements.append(summary_table)

    # ---- Bin utilization table ----
    if bin_rows and len(bin_rows) > 1:
        elements.append(Paragraph('Bin Utilization', heading_style))
        bin_table = Table(bin_rows, repeatRows=1)
        bin_table.setStyle(_table_style())
        elements.append(bin_table)

    # ---- Collection history table ----
    if collection_rows and len(collection_rows) > 1:
        elements.append(Paragraph('Collection History', heading_style))
        coll_table = Table(collection_rows, repeatRows=1)
        coll_table.setStyle(_table_style())
        elements.append(coll_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _table_style():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREEN]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ])
