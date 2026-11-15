"""Editable promotional SVG templates and PostgreSQL-powered content records.

This module handles promotional creative assets only. It does not automate
student eligibility, identity claims, or verification-document generation.
"""
import hashlib
import html
import json
import logging
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import psycopg
from psycopg.rows import dict_row

LOG = logging.getLogger("PPYXR.creatives")
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)
MAX_SVG = 5 * 1024 * 1024
FIELDS = {
    "title": "Title / headline",
    "subtitle": "Subtitle",
    "brand": "Brand",
    "product": "Product name",
    "price": "Price",
    "date": "Date",
    "contact_email": "Business contact email",
    "description": "Description",
    "cta": "Call to action",
}
TEXT_ELEMENTS = {"text", "tspan"}
ALLOWED_TAGS = {
    "svg", "g", "defs", "path", "rect", "circle", "ellipse",
    "line", "polygon", "polyline", "text", "tspan", "linearGradient",
    "radialGradient", "stop", "clipPath", "mask", "pattern",
    "filter", "feGaussianBlur", "feOffset", "feBlend", "feColorMatrix",
    "feComposite", "feFlood", "feMerge", "feMergeNode", "feDropShadow",
    "feComponentTransfer", "feFuncR", "feFuncG", "feFuncB", "feFuncA",
    "symbol", "use",
}
ALLOWED_ATTR = {
    "id", "viewBox", "width", "height", "version", "x", "y", "x1", "x2",
    "y1", "y2", "cx", "cy", "r", "rx", "ry", "d", "points", "transform",
    "fill", "fill-opacity", "fill-rule", "stroke", "stroke-width",
    "stroke-linecap", "stroke-linejoin", "stroke-dasharray",
    "stroke-dashoffset", "stroke-opacity", "opacity", "display",
    "visibility", "font-family", "font-size", "font-weight", "font-style",
    "text-anchor", "letter-spacing", "word-spacing", "dx", "dy",
    "dominant-baseline", "textLength", "lengthAdjust", "clip-path",
    "clip-rule", "mask", "filter", "offset", "stop-color", "stop-opacity",
    "gradientUnits", "gradientTransform", "spreadMethod",
    "patternUnits", "patternContentUnits", "patternTransform",
    "preserveAspectRatio", "color", "vector-effect", "stdDeviation",
    "in", "in2", "result", "mode", "operator", "values", "type",
    "slope", "intercept", "amplitude", "exponent", "k1", "k2", "k3", "k4",
    "flood-color", "flood-opacity",
}
SUGGESTIONS = {
    "price": ("price", "$", "€", "د.ت", "dinars", "prix"),
    "contact_email": ("contact@", "support@", "sales@", "business email"),
    "brand": ("brand", "logo", "company"),
    "product": ("product", "item", "service", "plan"),
    "title": ("title", "headline", "heading", "عنوان"),
    "subtitle": ("subtitle", "tagline"),
    "date": ("date", "تاريخ"),
    "description": ("description", "details", "تفاصيل"),
    "cta": ("buy", "order now", "learn more", "shop now", "اشتر"),
}


def _name(name):
    if not isinstance(name, str) or len(name) > 120 or len(name) < 5:
        raise ValueError("Invalid template name")
    if Path(name).name != name or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError("Invalid template name")
    if Path(name).suffix.lower() != ".svg":
        raise ValueError("Only SVG layers are editable with this version")
    return name


def _template(name):
    root = Path(os.getenv("TEMPLATE_STORAGE_DIR", "/data/templates"))
    p = root / _name(name)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_SVG:
        raise ValueError("Template unavailable or too large")
    return p


def _local(key):
    return key.rsplit("}", 1)[-1]


def _attr_ok(key, value):
    attr = _local(key)
    if attr == "href":
        return value.startswith("#") and len(value) < 200
    if attr not in ALLOWED_ATTR or len(value) > 10000:
        return False
    # No external styles, scripts, embedded images, or CSS functions.
    if re.search(r"javascript:|data:|https?://|file:|@import|expression|url\s*\(", value, re.I):
        if attr in {"fill", "stroke", "filter", "clip-path", "mask"}:
            return bool(re.fullmatch(r"\s*url\(\s*['\"]?#[a-zA-Z0-9_.:-]+['\"]?\s*\)\s*", value))
        return False
    return True


def _clean_svg(raw):
    if len(raw) > MAX_SVG:
        raise ValueError("SVG exceeds 5 MB")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("SVG with entities is not supported")
    try:
        original = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError("Invalid SVG") from exc
    if _local(original.tag) != "svg":
        raise ValueError("Expected SVG")
    count = [0]

    def convert(node, depth):
        count[0] += 1
        if count[0] > 12000 or depth > 60:
            raise ValueError("SVG complexity limit exceeded")
        tag = _local(node.tag)
        if tag not in ALLOWED_TAGS:
            return None
        result = ET.Element("{" + SVG_NS + "}" + tag)
        for key, value in node.attrib.items():
            val = str(value)
            if _attr_ok(key, val):
                if _local(key) == "href":
                    result.set("{" + XLINK_NS + "}href", val)
                else:
                    result.set(_local(key), val)
        if tag in TEXT_ELEMENTS:
            result.text = (node.text or "")[:500]
        for child in node:
            converted = convert(child, depth + 1)
            if converted is not None:
                result.append(converted)
                if tag in TEXT_ELEMENTS:
                    converted.tail = (child.tail or "")[:500]
        return result

    return convert(original, 0)


def layers(root):
    found = []
    for node in root.iter():
        if _local(node.tag) == "text":
            found.append(node)
    return found[:80]


def layer_description(node, idx):
    text = "".join(node.itertext()).strip()
    return {"index": idx, "label": text[:100] or f"Text layer {idx + 1}",
            "suggestion": guess_field(text)}


def guess_field(text):
    lower = text.lower()
    for field, needles in SUGGESTIONS.items():
        if any(needle.lower() in lower for needle in needles):
            return field
    return ""


def analyze(name):
    path = _template(name)
    raw = path.read_bytes()
    root = _clean_svg(raw)
    nodes = layers(root)
    return {
        "name": name,
        "checksum": hashlib.sha256(raw).hexdigest(),
        "layers": [layer_description(node, i) for i, node in enumerate(nodes)],
    }


def _db():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ValueError("PostgreSQL DATABASE_URL is missing")
    return psycopg.connect(url, connect_timeout=12)


def init_db():
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS creative_template_mappings (
                    template_name TEXT PRIMARY KEY,
                    source_checksum TEXT NOT NULL,
                    layer_map JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS creative_template_rows (
                    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    contents JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            cur.execute("""CREATE INDEX IF NOT EXISTS creative_template_rows_template_id
                           ON creative_template_rows (template_name, id DESC)""")


def mapping(name):
    _name(name)
    with _db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""SELECT source_checksum, layer_map
                           FROM creative_template_mappings WHERE template_name = %s""", (name,))
            result = cur.fetchone()
    return result


def save_mapping(name, checksum, selections):
    details = analyze(name)
    if checksum != details["checksum"]:
        raise ValueError("Template was replaced. Reload the mapping editor.")
    accepted = {}
    for idx, value in selections.items():
        if str(idx).isdigit() and int(idx) < len(details["layers"]) and value in FIELDS:
            accepted[str(int(idx))] = value
    if not accepted:
        raise ValueError("Select at least one editable layer")
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO creative_template_mappings (template_name, source_checksum, layer_map)
                VALUES (%s,%s,%s::jsonb)
                ON CONFLICT (template_name) DO UPDATE
                SET source_checksum=excluded.source_checksum,
                    layer_map=excluded.layer_map,
                    updated_at=now()
            """, (name, checksum, json.dumps(accepted)))
    return accepted


def saved_fields(name):
    info = mapping(name)
    if not info:
        return []
    if info["source_checksum"] != analyze(name)["checksum"]:
        return []
    return list(dict.fromkeys(info["layer_map"].values()))


def add_row(name, values):
    permitted = saved_fields(name)
    if not permitted:
        raise ValueError("Map and save template fields first")
    data = {}
    for field in permitted:
        value = str(values.get(field, "")).strip()
        if len(value) > 180:
            raise ValueError("Text values may not exceed 180 characters")
        data[field] = value
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO creative_template_rows (template_name, contents)
                VALUES (%s, %s::jsonb) RETURNING id
            """, (name, json.dumps(data)))
            return cur.fetchone()[0]


def get_rows(name, limit=25):
    _name(name)
    with _db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT id, contents, created_at FROM creative_template_rows
                WHERE template_name=%s ORDER BY id DESC LIMIT %s
            """, (name, min(max(int(limit), 1), 100)))
            return cur.fetchall()


def _values(name, row_id):
    with _db() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if row_id is None:
                cur.execute("""SELECT contents FROM creative_template_rows
                               WHERE template_name=%s ORDER BY id DESC LIMIT 1""", (name,))
            else:
                cur.execute("""SELECT contents FROM creative_template_rows
                               WHERE template_name=%s AND id=%s""", (name, int(row_id)))
            row = cur.fetchone()
    if not row:
        raise ValueError("No data row found")
    return row["contents"]


def render(name, row_id=None):
    cfg = mapping(name)
    if not cfg:
        raise ValueError("No field mapping saved")
    raw = _template(name).read_bytes()
    if cfg["source_checksum"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Template changed: remap its fields")
    root = _clean_svg(raw)
    nodes = layers(root)
    vals = _values(name, row_id)
    for index, field in cfg["layer_map"].items():
        idx = int(index)
        if idx >= len(nodes) or field not in FIELDS:
            continue
        item = nodes[idx]
        # Preserve the text element's existing size, coordinates, and fills.
        # Clear tspan text without removing geometric/style attributes.
        for element in item.iter():
            if _local(element.tag) in TEXT_ELEMENTS:
                element.text = ""
                if element is not item:
                    element.tail = ""
        item.text = str(vals.get(field, ""))[:180]
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def pristine_preview(name):
    return ET.tostring(_clean_svg(_template(name).read_bytes()),
                       encoding="utf-8", xml_declaration=True)
