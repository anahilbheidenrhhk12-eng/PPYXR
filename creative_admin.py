"""Authenticated HTML views for creative SVG field mapping and data records.

Called only from template_admin.py after cookie authorization.
"""
import html
import logging
from urllib.parse import parse_qs, quote

import creative_templates

LOG = logging.getLogger("PPYXR.creative_admin")


def error(handler, exc):
    from template_admin import _page
    LOG.warning("Creative template operation failed: %s", type(exc).__name__)
    body = (
        '<a href="/admin/templates">← Back to templates</a>'
        '<section class="card"><h2>Template error</h2>'
        '<div class="note error">' + html.escape(str(exc)[:250]) + '</div></section>'
    )
    handler._send(400, _page("Template error", body))


def editor(handler, session, name):
    from template_admin import _admin_key, _csrf, _page
    try:
        details = creative_templates.analyze(name)
        original = creative_templates.mapping(name)
        existing = (original["layer_map"] if original and
                    original["source_checksum"] == details["checksum"] else {})
        token = _csrf(_admin_key(), session)
        rows = []
        for layer in details["layers"]:
            idx = layer["index"]
            choice = existing.get(str(idx), layer["suggestion"])
            options = ['<option value="">— Keep original text —</option>']
            for key, label in creative_templates.FIELDS.items():
                options.append(
                    '<option value="' + key + '"'
                    + (' selected' if choice == key else '')
                    + '>' + html.escape(label) + '</option>'
                )
            rows.append(
                '<div class="row"><div style="min-width:200px;flex:1">'
                '<strong>Text layer ' + str(idx + 1) + '</strong>'
                '<p class="muted">' + html.escape(layer["label"]) + '</p></div>'
                '<div style="min-width:200px;flex:1"><label>Variable to insert</label>'
                '<select name="layer_' + str(idx) + '">'
                + "".join(options) + '</select></div></div>'
            )
        notice = ""
        if original and not existing:
            notice = '<div class="note error">Artwork changed; please remap its layers.</div>'
        if not rows:
            notice += (
                '<div class="note">No editable text was detected. Figma SVG export '
                'must preserve text instead of converting fonts to outlines.</div>'
            )
        body = (
            '<div class="top"><div><h1>🎨 Smart text mapping</h1>'
            '<small class="muted">' + html.escape(name) + '</small></div>'
            '<a class="btn" href="/admin/templates">← Template library</a></div>'
            '<section class="card"><h2>Template preview</h2>'
            '<img class="preview" alt="SVG preview" src="/admin/templates/artwork?name='
            + quote(name) + '">'
            '<p class="muted">Suggestions are based on visible labels. '
            'Review selections before saving.</p></section>'
            + notice +
            '<section class="card"><h2>Choose changing fields</h2>'
            '<form method="post" action="/admin/templates/map">'
            '<input type="hidden" name="csrf" value="' + token + '">'
            '<input type="hidden" name="name" value="' + html.escape(name, quote=True) + '">'
            '<input type="hidden" name="checksum" value="' + details["checksum"] + '">'
            + "".join(rows)
            + ('<button type="submit">Save field mapping</button>' if rows else '')
            + '</form></section><section class="card">'
            '<h2>Generate versions using PostgreSQL</h2>'
            '<p>After mapping fields, create promotional content records and '
            'generate unique copies of this design.</p>'
            '<a class="btn" href="/admin/templates/rows?name=' + quote(name)
            + '">Open content database</a></section>'
        )
        handler._send(200, _page("Smart template mapper", body))
    except Exception as exc:
        error(handler, exc)


def rows(handler, session, name):
    from template_admin import _admin_key, _csrf, _page
    try:
        keys = creative_templates.saved_fields(name)
        if not keys:
            handler._redirect("/admin/templates/edit?name=" + quote(name))
            return
        items = creative_templates.get_rows(name, 30)
        token = _csrf(_admin_key(), session)
        inputs = []
        for key in keys:
            label = creative_templates.FIELDS[key]
            inputs.append(
                '<label>' + html.escape(label) + '</label>'
                '<input type="text" maxlength="180" name="field_' + key
                + '" placeholder="' + html.escape(label, quote=True) + '">'
            )
        cards = []
        for item in items:
            summary = " · ".join(
                creative_templates.FIELDS.get(k, k) + ": " + str(v)[:40]
                for k, v in item["contents"].items()
            )
            cards.append(
                '<div class="row"><div style="flex:1"><strong>Content #'
                + str(item["id"]) + '</strong><p class="muted">'
                + html.escape(summary[:240]) + '</p></div><div class="actions">'
                '<a class="btn" href="/admin/templates/render?name='
                + quote(name) + '&id=' + str(item["id"])
                + '">Download generated SVG</a></div></div>'
            )
        body = (
            '<div class="top"><div><h1>📊 PostgreSQL content</h1>'
            '<small class="muted">' + html.escape(name) + '</small></div>'
            '<a class="btn" href="/admin/templates/edit?name='
            + quote(name) + '">← Edit field mapping</a></div>'
            '<section class="card"><h2>New content record</h2>'
            '<p class="muted">Each record produces a different version of '
            'this promotional design.</p>'
            '<form method="post" action="/admin/templates/record">'
            '<input type="hidden" name="csrf" value="' + token + '">'
            '<input type="hidden" name="name" value="' + html.escape(name, quote=True) + '">'
            + "".join(inputs)
            + '<button type="submit">Save to PostgreSQL</button></form></section>'
            '<section class="card"><h2>Saved content records</h2>'
            + ("".join(cards) or '<p class="muted">No records yet.</p>')
            + '</section>'
        )
        handler._send(200, _page("Creative content", body))
    except Exception as exc:
        error(handler, exc)


def do_get(handler, route, session):
    path = route.path
    name = (parse_qs(route.query).get("name") or [""])[0]
    if path == "/admin/templates/edit":
        editor(handler, session, name)
        return True
    if path == "/admin/templates/rows":
        rows(handler, session, name)
        return True
    if path in ("/admin/templates/artwork", "/admin/templates/render"):
        try:
            if path.endswith("/artwork"):
                data = creative_templates.pristine_preview(name)
                handler._send(200, data, "image/svg+xml; charset=utf-8")
            else:
                row = (parse_qs(route.query).get("id") or [None])[0]
                data = creative_templates.render(name, row)
                handler._send(
                    200, data, "image/svg+xml; charset=utf-8",
                    {"Content-Disposition":
                        "attachment; filename*=UTF-8''" + quote("generated-" + name)},
                )
        except Exception as exc:
            error(handler, exc)
        return True
    return False


def do_post(handler, path, fields):
    if path not in ("/admin/templates/map", "/admin/templates/record"):
        return False
    try:
        name = fields.get("name", "")
        if path.endswith("/map"):
            selected = {
                k[6:]: value for k, value in fields.items()
                if k.startswith("layer_") and value
            }
            creative_templates.save_mapping(name, fields.get("checksum", ""), selected)
            handler._redirect("/admin/templates/rows?name=" + quote(name))
        else:
            values = {k[6:]: value for k, value in fields.items()
                      if k.startswith("field_")}
            creative_templates.add_row(name, values)
            handler._redirect("/admin/templates/rows?name=" + quote(name))
    except Exception as exc:
        error(handler, exc)
    return True
