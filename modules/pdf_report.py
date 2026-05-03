"""
pdf_report.py  -  AgriGuard AI
Unicode-safe PDF with proper RTL rendering for Urdu/Arabic/Hindi.

One-time install:
    pip install reportlab arabic-reshaper python-bidi

Font location:
    agriGuard/fonts/NotoSansArabic-Regular.ttf
"""

import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Optional RTL support ──────────────────────────────────────
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    RTL_AVAILABLE = True
except ImportError:
    RTL_AVAILABLE = False

# ── Palette ───────────────────────────────────────────────────
GREEN_DEEP = HexColor("#1a3a2a")
GREEN_MID  = HexColor("#2d6a4f")
GOLD       = HexColor("#b45309")
TEXT_SOFT  = HexColor("#4a6741")
TEXT_GREY  = HexColor("#505050")

# ── RTL languages ─────────────────────────────────────────────
RTL_LANG_CODES = {"ur", "ar"}

# ── Font setup ────────────────────────────────────────────────
# pdf_report.py is inside agriGuard/modules/
# going one level up (..) reaches agriGuard/, then into fonts/
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
_FONT_PATH = os.path.join(_THIS_DIR, "..", "fonts", "NotoSansArabic-Regular.ttf")

_FONTS_LOADED = False

def _ensure_fonts():
    global _FONTS_LOADED
    if _FONTS_LOADED:
        return
    if os.path.isfile(_FONT_PATH):
        pdfmetrics.registerFont(TTFont("NotoArabic",      _FONT_PATH))
        pdfmetrics.registerFont(TTFont("NotoArabic-Bold", _FONT_PATH))
    _FONTS_LOADED = True

def _font(bold=False) -> str:
    _ensure_fonts()
    if os.path.isfile(_FONT_PATH):
        return "NotoArabic-Bold" if bold else "NotoArabic"
    return "Helvetica-Bold" if bold else "Helvetica"


# ── Text helpers ──────────────────────────────────────────────
def _safe(val, fallback="N/A") -> str:
    s = str(val).strip() if val else fallback
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")) or fallback


def _prepare(text, lang_code="en") -> str:
    """Reshape + BiDi for Urdu/Arabic; plain escape for everything else."""
    raw = str(text).strip() if text else "N/A"
    if lang_code in RTL_LANG_CODES:
        if RTL_AVAILABLE:
            raw = get_display(arabic_reshaper.reshape(raw))
        else:
            raw = raw + "  [install arabic-reshaper & python-bidi for correct display]"
    return _safe(raw)


# ── Paragraph styles ──────────────────────────────────────────
def _ps(name, size=10, bold=False, color=None, align=0, space_after=2):
    _ensure_fonts()
    return ParagraphStyle(
        name,
        fontName=_font(bold),
        fontSize=size,
        leading=size * 1.45,
        textColor=color or TEXT_GREY,
        alignment=align,
        spaceAfter=space_after,
    )

def _styles():
    return {
        "section": _ps("Sec", size=11, bold=True,  color=GREEN_MID, space_after=0),
        "weather": _ps("Wea", size=11, bold=True,  color=GOLD,      space_after=0),
        "label":   _ps("Lbl", size=9,  bold=True,  color=TEXT_GREY),
        "value":   _ps("Val", size=9,  bold=False, color=TEXT_GREY, space_after=4),
    }


# ── Section builder ───────────────────────────────────────────
def _section(story, title, rows, title_style, accent, lang_code="en"):
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=accent, spaceAfter=4))
    st = _styles()
    data = []
    for label, value in rows:
        data.append([
            Paragraph(f"{label}:", st["label"]),
            Paragraph(_prepare(value, lang_code), st["value"]),
        ])

    tbl = Table(data, colWidths=[38*mm, 132*mm])
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8*mm))


# ── Canvas callbacks ──────────────────────────────────────────
def _header(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(GREEN_DEEP)
    canvas.rect(0, A4[1] - 32*mm, A4[0], 32*mm, fill=1, stroke=0)
    canvas.setFont(_font(bold=True), 18)
    canvas.setFillColor(white)
    canvas.drawCentredString(A4[0] / 2, A4[1] - 18*mm,
                             "AgriGuard AI - Crop Diagnostic Report")
    canvas.setFont(_font(), 9)
    canvas.setFillColor(HexColor("#c8e6c9"))
    canvas.drawCentredString(
        A4[0] / 2, A4[1] - 26*mm,
        f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        "  |  Region: Karachi, Sindh",
    )
    canvas.restoreState()


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(_font(), 8)
    canvas.setFillColor(TEXT_SOFT)
    canvas.drawCentredString(A4[0] / 2, 14*mm,
                             "AgriGuard AI  |  SDG 1  |  SDG 2  |  SDG 13")
    canvas.drawCentredString(A4[0] / 2, 9*mm,
                             "AI-generated report. Consult an agronomist for critical decisions.")
    canvas.restoreState()


def _both(canvas, doc):
    _header(canvas, doc)
    _footer(canvas, doc)


# ── Public entry point ────────────────────────────────────────
def generate_report(vision: dict, agent: dict, weather: dict,
                    lang_code: str = "en") -> bytes:

    # ── DEBUG (remove these 3 lines once working) ─────────────
    print("Font path:", _FONT_PATH)
    print("Font exists:", os.path.isfile(_FONT_PATH))
    print("RTL available:", RTL_AVAILABLE)
    # ──────────────────────────────────────────────────────────

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=38*mm, bottomMargin=22*mm,
        leftMargin=15*mm, rightMargin=15*mm,
    )

    st = _styles()
    story = []

    _section(story, "Disease Identification", [
        ("Disease",    vision.get("disease_name")),
        ("Crop",       vision.get("crop_type")),
        ("Severity",   vision.get("severity")),
        ("Confidence", f"{int(vision.get('confidence', 0) * 100)}%"),
    ], st["section"], GREEN_MID, lang_code="en")

    _section(story, "Weather Context (Karachi)", [
        ("Condition",   weather.get("condition")),
        ("Humidity",    f"{weather.get('humidity_pct', 'N/A')}%"),
        ("Temperature", f"{weather.get('temperature_c', 'N/A')} C"),
        ("Advisory",    weather.get("advice")),
    ], st["weather"], GOLD, lang_code="en")

    _section(story, "Treatment Plan", [
        ("Action",      agent.get("treatment")),
        ("Precautions", agent.get("precautions")),
        ("Urgency",     agent.get("urgency")),
        ("Source",      agent.get("rag_source")),
    ], st["section"], GREEN_MID, lang_code=lang_code)

    doc.build(story, onFirstPage=_both, onLaterPages=_footer)
    return buf.getvalue()