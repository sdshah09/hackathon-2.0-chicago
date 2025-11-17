# pyright: reportMissingImports=false
"""
PDF Generation Service.
Generates PDF documents from text summaries.
"""

from __future__ import annotations

import io
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def generate_summary_pdf(
    summary_text: str,
    patient_name: Optional[str] = None,
    specialist_type: str = "general",
) -> bytes:
    """
    Generate a PDF document from summary text.
    
    Args:
        summary_text: The summary text to convert to PDF
        patient_name: Optional patient name for header
        specialist_type: Type of specialist for title
    
    Returns:
        PDF content as bytes
    """
    # Create a BytesIO buffer to hold PDF
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )
    
    # Container for PDF content
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1a1a1a',
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    # Heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT,
    )
    
    # Body style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor='#333333',
        spaceAfter=6,
        alignment=TA_LEFT,
        leading=14,
    )
    
    # Add title
    title = f"Patient Health Summary - {specialist_type.title()}"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Add patient name if provided
    if patient_name:
        patient_para = Paragraph(f"<b>Patient:</b> {patient_name}", body_style)
        story.append(patient_para)
        story.append(Spacer(1, 0.1 * inch))
    
    # Helper function to convert markdown to HTML for ReportLab
    def markdown_to_html(text: str) -> str:
        """Convert markdown formatting to HTML for ReportLab Paragraph."""
        # Remove markdown bold (**text** or __text__)
        import re
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        # Remove markdown italic (*text* or _text_)
        text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
        text = re.sub(r'(?<!_)_(?!_)(.*?)(?<!_)_(?!_)', r'<i>\1</i>', text)
        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        # But preserve our HTML tags
        text = text.replace('&amp;lt;', '&lt;').replace('&amp;gt;', '&gt;')
        text = text.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        text = text.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        return text
    
    # Parse and add summary content
    lines = summary_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.05 * inch))
            continue
        
        # Check if line is a section header (starts with ## or is a heading)
        if line.startswith('##'):
            # Section header
            section_title = line.replace('##', '').strip()
            # Remove markdown from section title
            section_title = section_title.replace('**', '').replace('__', '')
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(section_title, heading_style))
            current_section = section_title
        elif line.startswith('#'):
            # Main heading
            heading = line.replace('#', '').strip()
            heading = heading.replace('**', '').replace('__', '')
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(heading, heading_style))
        elif line.startswith('-') or line.startswith('•'):
            # Bullet point
            bullet_text = line.lstrip('- •').strip()
            # Convert markdown to HTML
            bullet_text = markdown_to_html(bullet_text)
            para = Paragraph(f"• {bullet_text}", body_style)
            story.append(para)
        else:
            # Regular paragraph
            # Convert markdown to HTML
            formatted_line = markdown_to_html(line)
            para = Paragraph(formatted_line, body_style)
            story.append(para)
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

