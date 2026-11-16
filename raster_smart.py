"""OCR-backed, conservative layout suggestions for marketing artwork.

Only known promotional text labels are returned as editable overlays.
Images resembling personal credentials or student documents are not mapped.
Source images are analyzed locally; no text/images are sent to external APIs.
"""
import logging
import math
import re
import threading
from PIL import Image, ImageOps

from raster_creatives import describe, source_path

LOG = logging.getLogger("PPYXR.smart_layout")
_MODEL = None
_LOCK = threading.Lock()
MAX_SCAN_SIZE = 1600
MAX_SUGGESTIONS = 6
MIN_SCORE = .54

# Deliberately strict: a detected identity-style layout is not a
# promotional template even when it contains large headings or numbers.
_IDENTITY_TERMS = re.compile(
    r"\b(?:university|student|campus id|school id|college id|"
    r"university id|faculty id|umid|student no|student number|"
    r"card\s*(?:no\.?|number|#)|id\s*(?:number|no\.?|#)|"
    r"date of birth|birthdate|passport|driver.?s license|"
    r"issued by|government of|national identity|license number|"
    r"identity card|mcard)\b",
    re.IGNORECASE,
)
_PROMOTIONAL_TERMS = re.compile(
    r"\b(?:sale|discount|special offer|offer|limited time|"
    r"shop now|buy now|order now|book now|buy|shop|save|"
    r"new collection|collection|promotion|promo|campaign|"
    r"free shipping|subscribe|sign up|learn more|"
    r"get started|launch|deals|early bird)\b",
    re.IGNORECASE,
)
_PROMO_ACTION = re.compile(
    r"\b(?:shop|buy|order|subscribe|sign up|"
    r"learn more|get started|book now|join now)\b",
    re.IGNORECASE,
)
_PRICE = re.compile(
    r"(?:[$€£]\s*\d|\b(?:USD|EUR|TND|GBP)\s*\d|\b\d+[\.,]?\d*\s*(?:USD|EUR|TND|GBP)\b)",
    re.IGNORECASE,
)
_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_WEB = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_DISCOUNT = re.compile(r"\b(?:SAVE|OFF|DISCOUNT|DEAL)\b|(?:\d+\s*%)", re.IGNORECASE)


def _model():
    global _MODEL
    if _MODEL is None:
        from rapidocr import RapidOCR
        _MODEL = RapidOCR()
    return _MODEL


def _norm_box(points, width, height):
    xcoords = [float(p[0]) for p in points]
    ycoords = [float(p[1]) for p in points]
    x1 = min(xcoords)
    x2 = max(xcoords)
    y1 = min(ycoords)
    y2 = max(ycoords)
    padx = max(2, (x2 - x1) * .07)
    pady = max(2, (y2 - y1) * .3)
    x1 = max(0, x1 - padx)
    y1 = max(0, y1 - pady)
    x2 = min(width, x2 + padx)
    y2 = min(height, y2 + pady)
    x = round(1000 * x1 / width, 2)
    y = round(1000 * y1 / height, 2)
    w = round(1000 * (x2 - x1) / width, 2)
    h = round(1000 * (y2 - y1) / height, 2)
    if w < 15:
        gap = 15 - w
        x = max(0, x - gap / 2)
        w = min(1000 - x, 15)
    if h < 15:
        gap = 15 - h
        y = max(0, y - gap / 2)
        h = min(1000 - y, 15)
    if x + w > 1000:
        x = round(1000 - w, 2)
    if y + h > 1000:
        y = round(1000 - h, 2)
    size = max(9, min(90, round(1000 * (y2 - y1) * .75 / width)))
    return {"x": round(x, 2), "y": round(y, 2), "w": round(w, 2),
            "h": round(h, 2), "size": size}


def suggest(name):
    """Return only supported promotional field boxes detected by true OCR."""
    describe(name)
    with Image.open(source_path(name)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((MAX_SCAN_SIZE, MAX_SCAN_SIZE))
        width, height = image.size
        with _LOCK:
            result = _model()(image, use_cls=False)
    boxes = getattr(result, "boxes", None)
    txts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if boxes is None or txts is None or scores is None:
        return {"suggestions": [], "message": "No readable text was detected in the image."}
    lines = []
    for points, text, confidence in zip(boxes, txts, scores):
        try:
            value = str(text).strip()
            probability = float(confidence)
            if not value or not math.isfinite(probability) or probability < MIN_SCORE:
                continue
            geometry = _norm_box(points, width, height)
            lines.append({"text": value[:100], "confidence": probability, **geometry})
        except (ValueError, TypeError, IndexError, ZeroDivisionError):
            continue
    if not lines:
        return {"suggestions": [], "message": "No confident text recognition was possible."}

    all_text = " ".join(line["text"] for line in lines)
    if _IDENTITY_TERMS.search(all_text):
        return {"suggestions": [], "message":
                "This layout is handled in read-only analysis mode. No editable text regions were suggested."}
    # Require an actual promotion signal. A regular photograph or document
    # must not receive invented labels such as 'Price' or 'Call to action'.
    if not (_PROMOTIONAL_TERMS.search(all_text) or _PRICE.search(all_text)):
        return {"suggestions": [], "message":
                "OCR found text, but no promotional labels could be identified confidently. Nothing was placed."}

    chosen = []
    used = set()

    def assign(field, line):
        if field in used or len(chosen) >= MAX_SUGGESTIONS:
            return
        data = {k: line[k] for k in ("x", "y", "w", "h", "size")}
        data.update({"field": field, "shape": "rect", "color": "#FFFFFF",
                     "bold": field in ("title", "price", "cta", "discount_label"),
                     "align": "left", "confidence": round(line["confidence"], 2),
                     "detected": line["text"]})
        chosen.append(data)
        used.add(field)

    for line in sorted(lines, key=lambda obj: -obj["confidence"]):
        text = line["text"]
        if _PRICE.search(text):
            assign("price", line)
        elif _DISCOUNT.search(text):
            assign("discount_label", line)
        elif _PROMO_ACTION.search(text):
            assign("cta", line)
        elif _EMAIL.search(text):
            assign("contact_email", line)
        elif _WEB.search(text):
            assign("website", line)

    # Largest unassigned line is likely the campaign headline, but only in an
    # image with independently recognized promotional content.
    remaining = [line for line in lines if not any(
        line["text"] == item["detected"] for item in chosen
    ) and len(line["text"]) >= 5]
    remaining.sort(key=lambda line: (
        -line["h"], line["y"], -line["confidence"]
    ))
    if remaining:
        assign("title", remaining[0])
    if len(remaining) > 1:
        assign("subtitle", remaining[1])
    if not chosen:
        return {"suggestions": [], "message":
                "No promotional text fields could be assigned from OCR."}
    return {"suggestions": chosen, "message":
            f"OCR matched {len(chosen)} promotional text regions. Review them before saving."}
