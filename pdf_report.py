from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_pricing_pdf(markdown):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = []
    for line in markdown.splitlines():
        if not line.strip():
            story.append(Spacer(1, 5))
            continue
        level = len(line) - len(line.lstrip("#"))
        style = styles["Title" if level == 1 else "Heading2" if level else "BodyText"]
        text = line.lstrip("# ").replace("**", "").replace("`", "")
        story.append(Paragraph(escape(text), style))
    SimpleDocTemplate(buffer, title="Comprehensive Pricing Report").build(story)
    return buffer.getvalue()
