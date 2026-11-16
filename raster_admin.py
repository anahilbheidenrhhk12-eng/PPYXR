"""Admin-only visual overlay editor for promotional PNG/JPG/WEBP artwork."""
import hmac
import html
import json
import logging
from urllib.parse import parse_qs, quote

import admin_ui
import raster_creatives
import raster_smart

LOG = logging.getLogger("PPYXR.raster_admin")


def esc(value):
    return html.escape(str(value), quote=True)


def failure(handler, exc):
    from template_admin import _page
    LOG.warning("Visual editor request failed: %s", type(exc).__name__)
    body = (
        '<div class="heading-row"><div><div class="eyebrow">IMAGE STUDIO</div>'
        '<h1>Unable to complete request</h1>'
        '<p>The original uploaded image is unchanged.</p></div></div>'
        '<section class="panel"><div class="note error">' + esc(str(exc)[:250])
        + '</div><a class="btn btn-secondary" href="/admin/templates?view=library">'
        + admin_ui.icon("layers", 15) + ' Back to library</a></section>'
    )
    handler._send(400, _page("Visual editor", body, active="library"))


def editor(handler, session, name):
    from template_admin import _page, _csrf, _admin_key
    try:
        info = raster_creatives.describe(name)
        existing = raster_creatives.mapping(name)
        stale = existing is not None and existing["source_checksum"] != info["checksum"]
        layers = existing["overlays"] if existing and not stale else []
        token = _csrf(_admin_key(), session)
        fields = raster_creatives.FIELDS
        options = "".join(
            '<option value="' + esc(key) + '">' + esc(label) + '</option>'
            for key, label in fields.items()
        )
        field_json = esc(json.dumps(fields, ensure_ascii=False, separators=(",", ":")))
        config_json = esc(json.dumps({"overlays": layers}, ensure_ascii=False, separators=(",", ":")))
        controls = (
            '<div class="raster-toolbar">'
            '<button class="btn" type="button" data-draw>'
            + admin_ui.icon("plus", 15) + ' Draw text area</button>'
            '<button class="toolbar-button" type="button" data-auto>'
            + admin_ui.icon("sparkle", 15) + ' Detect marketing text (OCR)</button>'
            '<button class="toolbar-button" type="button" data-polygon>'
            + admin_ui.icon("edit", 14) + ' Polygon</button>'
            '<button class="toolbar-button" type="button" data-lasso>'
            + admin_ui.icon("layers", 14) + ' Freehand lasso</button>'
            '<button class="toolbar-button" type="button" data-finish-shape>'
            + admin_ui.icon("check", 14) + ' Finish polygon</button>'
            '<button class="toolbar-button" type="button" data-cancel-shape>'
            + admin_ui.icon("trash", 14) + ' Cancel</button>'
            '<button class="toolbar-button" type="button" data-preview aria-pressed="false">'
            + admin_ui.icon("image", 15) + ' Sample preview</button>'
            '</div>'
        )
        body = (
            '<div class="heading-row"><div><div class="eyebrow">VISUAL IMAGE STUDIO</div>'
            '<h1>Design your dynamic image</h1>'
            '<p>Draw editable promotional text regions directly on a JPG, PNG or WEBP. '
            'Connect them to your own PostgreSQL content, without changing the source image.</p>'
            '</div><div class="heading-actions">'
            '<a class="btn btn-secondary" href="/admin/templates?view=library">'
            + admin_ui.icon("layers", 16) + ' Library</a>'
            '<a class="btn" href="/admin/templates/raster/records?name=' + quote(name)
            + '">' + admin_ui.icon("database", 16) + ' Content records</a></div></div>'
            + ('<div class="note error">This image was replaced after the last save. '
               'The old mapping is hidden; create new regions for this version.</div>'
               if stale else '')
            + '<div class="raster-grid" data-raster-editor data-name="' + esc(name)
            + '" data-csrf="' + esc(token) + '" data-checksum="'
            + esc(info["checksum"]) + '" data-fields="' + field_json
            + '" data-config="' + config_json
            + '" data-image="/admin/templates/thumb?name=' + esc(quote(name)) + '">'
            '<section class="raster-canvas-shell"><div class="raster-canvas-top">'
            '<div><h2>Artwork preview</h2><p style="font-size:11px;margin-top:4px">'
            + esc(name) + ' · ' + str(info["width"]) + ' × '
            + str(info["height"]) + ' px</p></div><span class="badge purple">'
            + admin_ui.icon("sparkle", 14) + ' Interactive canvas</span></div>'
            '<div class="raster-stage"><canvas data-raster-canvas '
            'aria-label="Visual editor image canvas"></canvas></div>'
            '<div class="raster-canvas-footer"><span>Drag to draw · Select to move · '
            'Drag the lower-right corner to resize</span>'
            '<span class="badge">' + str(info["width"]) + ' × '
            + str(info["height"]) + ' px</span></div></section>'
            '<div class="raster-side">'
            '<section class="panel"><div class="panel-head"><div>'
            '<h2>Text regions</h2>'
            '<p>Each area connects to a content field</p></div></div>'
            + controls +
            '<div class="raster-divider"></div>'
            '<div class="raster-tip">' + admin_ui.icon("info", 15)
            + '<span>Text detection reads the uploaded artwork and suggests regions only when '
            'promotional text is recognized. It does not place random labels in blank areas. '
            'Always review the results before saving.</span></div>'
            '<div class="raster-layer-list" data-raster-layers></div>'
            '<div class="raster-toolbar" style="margin-top:12px">'
            '<button class="toolbar-button" type="button" data-undo>'
            + admin_ui.icon("clock", 14) + ' Undo</button>'
            '<button class="toolbar-button" type="button" data-delete>'
            + admin_ui.icon("trash", 14) + ' Delete selected</button>'
            '</div>'
            '<div class="field raster-field-picker"><label>FIELD FOR NEW REGIONS</label>'
            '<select data-add-field>' + options + '</select></div></section>'
            '<section class="panel"><div class="panel-head"><div>'
            '<h2>Selected region</h2>'
            '<p>Text style, alignment and field</p></div></div>'
            '<div class="raster-properties" data-raster-props hidden>'
            '<div class="field"><label>SELECTED: '
            '<span data-selected-label>—</span></label></div>'
            '<div class="raster-property-grid">'
            '<div class="field"><label>CONTENT FIELD</label>'
            '<select data-field>' + options + '</select></div>'
            '<div class="field"><label>FONT SIZE</label>'
            '<input data-size type="number" min="8" max="120" value="34"></div>'
            '<div class="field"><label>TEXT COLOR</label>'
            '<input data-color type="color" value="#ffffff"></div>'
            '<div class="field"><label>ALIGNMENT</label>'
            '<select data-align><option value="left">Left</option>'
            '<option value="center">Center</option>'
            '<option value="right">Right</option></select></div></div>'
            '<label class="raster-checkbox"><input data-bold type="checkbox"> '
            'Bold promotional text</label></div>'
            '<div class="raster-notice" data-no-props>Select a text region on '
            'the image to adjust its appearance.</div>'
            '</section>'
            '<section class="panel raster-editor-actions"><h2>Save your layout</h2>'
            '<p style="font-size:12px;margin:8px 0 14px">'
            'Text regions and their field assignments are stored in PostgreSQL. '
            'The image remains unchanged.</p>'
            '<button class="btn" type="button" data-save-json data-raster-save>'
            + admin_ui.icon("check", 16) + ' Save visual mapping</button>'
            '<div class="raster-status" data-raster-status role="status" aria-live="polite">'
            '</div>'
            '<a class="btn btn-secondary" data-continue style="display:none" '
            'href="/admin/templates/raster/records?name=' + quote(name) + '">'
            + admin_ui.icon("arrow", 16) + ' Add content and generate</a>'
            '</section></div></div>'
            '<div class="note" style="margin-top:20px">'
            + admin_ui.icon("info", 16)
            + ' This editor overlays new promotional text on the artwork. '
            'It does not erase text baked into the image or replace faces.</div>'
            '<script defer src="/admin/assets/raster.js"></script>'
            '<script defer src="/admin/assets/raster-shapes.js"></script>'
        )
        handler._send(200, _page("Visual image editor", body, active="library"))
    except Exception as exc:
        failure(handler, exc)


def records_page(handler, session, name, edit_id=None):
    from template_admin import _page, _csrf, _admin_key
    try:
        info = raster_creatives.describe(name)
        keys = raster_creatives.saved_fields(name)
        if not keys:
            handler._redirect("/admin/templates/raster/edit?name=" + quote(name))
            return
        rows = raster_creatives.records(name, 100)
        editing = raster_creatives.get_record(name, edit_id) if edit_id else None
        token = _csrf(_admin_key(), session)
        inputs = []
        for field in keys:
            label = raster_creatives.FIELDS[field]
            text = editing["contents"].get(field, "") if editing else ""
            inputs.append(
                '<div class="field"><label>' + esc(label).upper() + '</label>'
                '<input type="text" maxlength="180" name="field_' + esc(field)
                + '" value="' + esc(text) + '" placeholder="Enter '
                + esc(label) + '"></div>'
            )
        row_markup = []
        for row in rows:
            row_id = str(row["id"])
            content = " · ".join(
                raster_creatives.FIELDS.get(k, k) + ": " + str(v)[:34]
                for k, v in row["contents"].items()
            )
            row_markup.append(
                '<tr><td class="name-cell">#' + row_id + '</td>'
                '<td>' + esc(content[:160]) + '</td>'
                '<td><span class="badge green">Ready</span></td>'
                '<td><div class="actions">'
                '<a class="btn btn-secondary" target="_blank" rel="noreferrer" '
                'href="/admin/templates/raster/preview?name=' + quote(name)
                + '&id=' + row_id + '">'
                + admin_ui.icon("image", 14) + ' Preview</a>'
                '<a class="btn btn-secondary" title="Download generated PNG" '
                'href="/admin/templates/raster/download?name=' + quote(name)
                + '&id=' + row_id + '">'
                + admin_ui.icon("download", 14) + '</a>'
                '<a class="btn btn-secondary" title="Edit content" '
                'href="/admin/templates/raster/records?name=' + quote(name)
                + '&edit=' + row_id + '">'
                + admin_ui.icon("edit", 14) + '</a>'
                '<form class="inline" method="post" '
                'action="/admin/templates/raster/delete_record" '
                'data-confirm="Permanently delete this promotional content record?">'
                '<input type="hidden" name="csrf" value="' + esc(token) + '">'
                '<input type="hidden" name="name" value="' + esc(name) + '">'
                '<input type="hidden" name="id" value="' + row_id + '">'
                '<button type="submit" class="btn btn-danger" title="Delete record">'
                + admin_ui.icon("trash", 14) + '</button></form>'
                '</div></td></tr>'
            )
        record_route = (
            "/admin/templates/raster/update_record" if editing else
            "/admin/templates/raster/add_record"
        )
        form = (
            '<form method="post" action="' + record_route + '">'
            '<input type="hidden" name="csrf" value="' + esc(token) + '">'
            '<input type="hidden" name="name" value="' + esc(name) + '">'
            + ('<input type="hidden" name="id" value="' + str(editing["id"]) + '">'
               if editing else '')
            + '<div class="form-row">' + "".join(inputs) + '</div>'
            '<div class="form-actions">'
            '<button type="submit">' + admin_ui.icon("check", 16)
            + (' Save changes' if editing else ' Add content record') + '</button>'
            + ('<a class="btn btn-secondary" href="/admin/templates/raster/records?name='
               + quote(name) + '">Cancel edit</a>' if editing else '')
            + '</div></form>'
        )
        body = (
            '<div class="heading-row"><div><div class="eyebrow">IMAGE GENERATOR</div>'
            '<h1>Dynamic promotional image versions</h1>'
            '<p>Add different marketing content records and generate a new PNG '
            'for each record while preserving the artwork.</p></div>'
            '<div class="heading-actions">'
            '<a class="btn btn-secondary" href="/admin/templates/raster/edit?name='
            + quote(name) + '">'
            + admin_ui.icon("edit", 16) + ' Visual mapping</a>'
            '<a class="btn" href="/admin/templates/raster/next?name=' + quote(name)
            + '">' + admin_ui.icon("bolt", 16) + ' Generate next version</a>'
            '<a class="btn btn-secondary" href="/admin/templates/raster/batch?count=10&name='
            + quote(name) + '">'
            + admin_ui.icon("download", 16) + ' Export 10 PNGs (.zip)</a>'
            '</div></div>'
            '<div class="two-columns">'
            '<section class="panel"><div class="panel-head"><div><h2>'
            + ('Edit content #' + str(editing["id"]) if editing else 'Add a new version')
            + '</h2><p>Connected fields are taken from the visual mapper.</p>'
            '</div><span class="badge purple">' + str(len(keys))
            + ' variable fields</span></div>' + form + '</section>'
            '<section class="panel"><div class="panel-head"><div>'
            '<h2>Original image</h2><p>' + esc(name) + ' · '
            + str(info["width"]) + ' × ' + str(info["height"]) + ' px</p></div></div>'
            '<img class="preview" src="/admin/templates/thumb?name='
            + quote(name) + '" alt="Original promotional template">'
            '<div class="raster-notice" style="margin-top:15px">'
            'The Generate next button walks through the saved content records '
            'in order and wraps to the first record.</div></section></div>'
            '<section class="panel"><div class="panel-head"><div>'
            '<h2>Saved promotional versions</h2>'
            '<p>Each record produces its own generated image.</p></div>'
            '<span class="badge">' + str(len(rows)) + ' shown</span></div>'
            '<div class="table-scroll"><table class="data-table"><thead><tr>'
            '<th>ID</th><th>Content</th><th>Status</th><th>Actions</th>'
            '</tr></thead><tbody>'
            + ("".join(row_markup) if row_markup else
               '<tr><td colspan="4"><p class="muted">'
               'No records yet. Add your first promotional content record above.'
               '</p></td></tr>')
            + '</tbody></table></div></section>'
        )
        handler._send(200, _page("Image content", body, active="records"))
    except Exception as exc:
        failure(handler, exc)


def do_get(handler, route, session):
    path = route.path
    if not path.startswith("/admin/templates/raster/"):
        return False
    params = parse_qs(route.query)
    name = (params.get("name") or [""])[0]
    if path == "/admin/templates/raster/suggest":
        try:
            result = raster_smart.suggest(name)
            payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
            handler._send(200, payload, "application/json; charset=utf-8", {
                "Cache-Control": "no-store"
            })
        except Exception as exc:
            LOG.warning("Smart OCR failed: %s", type(exc).__name__)
            body = json.dumps({"error": "OCR is temporarily unavailable for this image"}).encode("utf-8")
            handler._send(503, body, "application/json; charset=utf-8", {
                "Cache-Control": "no-store"
            })
        return True
    if path == "/admin/templates/raster/edit":
        editor(handler, session, name)
        return True
    if path == "/admin/templates/raster/records":
        records_page(handler, session, name, (params.get("edit") or [None])[0])
        return True
    if path in (
        "/admin/templates/raster/preview",
        "/admin/templates/raster/download",
        "/admin/templates/raster/next",
        "/admin/templates/raster/batch",
    ):
        try:
            if path.endswith("/batch"):
                count = (params.get("count") or ["10"])[0]
                data = raster_creatives.export_batch(name, count)
                handler._send(200, data, "application/zip", {
                    "Content-Disposition": "attachment; filename*=UTF-8''"
                    + quote("promo-batch-" + name.rsplit(".", 1)[0] + ".zip")
                })
                return True
            if path.endswith("/next"):
                row_id, data = raster_creatives.next_version(name)
            else:
                row_id = (params.get("id") or [""])[0]
                data = raster_creatives.render(name, row_id)
            headers = None
            if not path.endswith("/preview"):
                filename = "promo-" + str(row_id) + "-" + name.rsplit(".", 1)[0] + ".png"
                headers = {
                    "Content-Disposition": "attachment; filename*=UTF-8''"
                    + quote(filename)
                }
            handler._send(200, data, "image/png", headers)
        except Exception as exc:
            failure(handler, exc)
        return True
    return False


def do_post_json(handler, route, body, expected_csrf):
    if route != "/admin/templates/raster/save":
        return False
    try:
        if len(body) > 96 * 1024:
            raise ValueError("Visual mapping data is too large")
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Expected JSON mapping")
        if not hmac.compare_digest(str(data.get("csrf", "")), expected_csrf):
            handler._send(403, b'{"error":"Invalid form token"}', "application/json")
            return True
        layers = raster_creatives.save_mapping(
            data.get("name", ""), data.get("checksum", ""), data.get("layers", [])
        )
        response = json.dumps({"ok": True, "saved": len(layers)}).encode("utf-8")
        handler._send(200, response, "application/json")
    except Exception as exc:
        response = json.dumps({"error": str(exc)[:240]}).encode("utf-8")
        handler._send(400, response, "application/json")
    return True


def do_post_form(handler, path, fields):
    if path not in (
        "/admin/templates/raster/add_record",
        "/admin/templates/raster/update_record",
        "/admin/templates/raster/delete_record",
    ):
        return False
    try:
        name = fields.get("name", "")
        if path.endswith("/delete_record"):
            raster_creatives.delete_record(name, fields.get("id", ""))
        else:
            values = {
                key[6:]: value for key, value in fields.items()
                if key.startswith("field_")
            }
            if path.endswith("/update_record"):
                raster_creatives.update_record(name, fields.get("id", ""), values)
            else:
                raster_creatives.add_record(name, values)
        handler._redirect("/admin/templates/raster/records?name=" + quote(name))
    except Exception as exc:
        failure(handler, exc)
    return True
