"""Professional creative editor and PostgreSQL content screens.

All routes are called only after TemplateAdminHandler checks the admin session.
"""
import csv
import html
import io
import logging
from urllib.parse import parse_qs, quote

import admin_ui
import creative_templates

LOG = logging.getLogger("PPYXR.creative_admin")


def esc(value):
    return html.escape(str(value), quote=True)


def error(handler, exc):
    from template_admin import _page
    LOG.warning("Creative editor failed: %s", type(exc).__name__)
    body = (
        '<div class="heading-row"><div><div class="eyebrow">REQUEST NOT COMPLETED</div>'
        '<h1>Could not process template</h1>'
        '<p>The original assets and existing content were not changed.</p>'
        '</div><a class="btn btn-secondary" href="/admin/templates?view=library">'
        + admin_ui.icon("layers", 16) + ' Back to library</a></div>'
        '<section class="panel"><div class="note error">'
        + admin_ui.icon("info", 16) + ' ' + esc(str(exc)[:260])
        + '</div></section>'
    )
    handler._send(400, _page("Template editor", body, active="library"))


def editor(handler, session, name):
    from template_admin import _admin_key, _csrf, _page
    try:
        details = creative_templates.analyze(name)
        saved = creative_templates.mapping(name)
        current = (
            saved["layer_map"] if saved and
            saved["source_checksum"] == details["checksum"] else {}
        )
        token = _csrf(_admin_key(), session)
        selected_count = len(current)
        rows = []
        for layer in details["layers"]:
            index = layer["index"]
            chosen = current.get(str(index), layer["suggestion"])
            options = ['<option value="">Keep original text</option>']
            for field, label in creative_templates.FIELDS.items():
                options.append(
                    '<option value="' + esc(field) + '"'
                    + (' selected' if field == chosen else "")
                    + '>' + esc(label) + '</option>'
                )
            rows.append(
                '<div class="layer-row" data-layer-row data-text="'
                + esc(layer["label"]) + '">'
                '<div><span class="layer-number">TEXT LAYER '
                + str(index + 1) + '</span><strong class="layer-text" title="'
                + esc(layer["label"]) + '">' + esc(layer["label"]) + '</strong>'
                + ('<div style="margin-top:6px"><span class="badge purple">'
                   + admin_ui.icon("sparkle", 12)
                   + ' Auto suggestion</span></div>'
                   if layer["suggestion"] and str(index) not in current else '')
                + '</div><div><label for="layer_' + str(index)
                + '">DATA FIELD</label>'
                '<select id="layer_' + str(index) + '" name="layer_'
                + str(index) + '" data-suggestion="' + esc(layer["suggestion"])
                + '">' + "".join(options) + '</select></div></div>'
            )
        notice = ""
        if saved and not current:
            notice = (
                '<div class="note error">' + admin_ui.icon("info", 15)
                + ' The SVG was changed since fields were configured. '
                'Please review the mappings again.</div>'
            )
        if not rows:
            notice += (
                '<div class="note">' + admin_ui.icon("info", 15)
                + ' No editable text layers detected. Export the Figma frame as '
                'SVG with text preserved. Text outlined into paths cannot be mapped.</div>'
            )
        action = (
            '<button type="submit">' + admin_ui.icon("check", 16)
            + ' Save field mapping</button>' if rows else ''
        )
        toolbar = (
            '<a class="btn btn-secondary" href="/admin/templates?view=library">'
            + admin_ui.icon("layers", 16) + ' Library</a>'
            '<a class="btn" href="/admin/templates/rows?name=' + quote(name)
            + '">' + admin_ui.icon("database", 16) + ' Content records</a>'
        )
        body = (
            '<div class="heading-row"><div><div class="eyebrow">SMART SVG EDITOR</div>'
            '<h1>Configure editable fields</h1>'
            '<p>Choose exactly which text layers change between generated '
            'versions. The rest of the artwork stays unchanged.</p></div>'
            '<div class="heading-actions">' + toolbar + '</div></div>'
            '<div class="editor-grid">'
            '<section class="panel preview-panel">'
            '<div class="panel-head"><div><h2>Design preview</h2>'
            '<p>' + esc(name) + '</p></div>'
            '<span class="badge purple">' + str(len(details["layers"]))
            + ' text layers</span></div>'
            '<div class="preview-stage"><img alt="Sanitized SVG template" '
            'src="/admin/templates/artwork?name=' + quote(name)
            + '"></div>'
            '<div class="setting"><div><strong>Original design</strong>'
            '<small>SVG layout preserved on export</small></div>'
            '<span class="badge green">' + admin_ui.icon("check", 12)
            + ' Available</span></div>'
            '<div class="setting"><div><strong>Saved mappings</strong>'
            '<small>Fields currently configured</small></div>'
            '<span class="badge">' + str(selected_count) + ' active</span></div>'
            '<a class="btn btn-secondary" style="margin-top:18px;width:100%" '
            'href="/admin/templates/file?name=' + quote(name) + '">'
            + admin_ui.icon("download", 16) + ' Download original</a>'
            '</section>'
            '<section class="panel">'
            '<div class="panel-head"><div><h2>Text layer mapping</h2>'
            '<p>Select data fields to replace the original text</p></div>'
            '<span class="badge">' + str(len(details["layers"])) + ' detected</span>'
            '</div>' + notice
            + '<div class="toolbar" style="margin-bottom:15px">'
            '<div class="searchbox" style="min-width:190px">'
            + admin_ui.icon("search", 15)
            + '<input data-layer-search type="text" '
            'placeholder="Search detected text..." aria-label="Search detected layers">'
            '</div>'
            '<button type="button" class="toolbar-button" data-mapping-suggest>'
            + admin_ui.icon("sparkle", 14) + ' Auto-fill</button>'
            '<button type="button" class="toolbar-button" data-mapping-clear>'
            'Clear all</button></div>'
            '<form method="post" action="/admin/templates/map">'
            '<input type="hidden" name="csrf" value="' + esc(token) + '">'
            '<input type="hidden" name="name" value="' + esc(name) + '">'
            '<input type="hidden" name="checksum" value="' + esc(details["checksum"]) + '">'
            + ("".join(rows) if rows else "")
            + '<div class="form-actions">' + action + '</div>'
            '</form></section></div>'
            '<div class="note" style="margin-top:20px">'
            + admin_ui.icon("info", 15)
            + ' Smart suggestions help identify editable promotional text, '
            'but you decide which fields are actually replaced.</div>'
        )
        handler._send(200, _page("SVG editor", body, active="library"))
    except Exception as exc:
        error(handler, exc)


def rows(handler, session, name, edit_id=None):
    from template_admin import _admin_key, _csrf, _page
    try:
        keys = creative_templates.saved_fields(name)
        if not keys:
            handler._redirect("/admin/templates/edit?name=" + quote(name))
            return
        items = creative_templates.get_rows(name, 100)
        existing = creative_templates.get_row(name, edit_id) if edit_id else None
        token = _csrf(_admin_key(), session)
        form_fields = []
        for key in keys:
            label = creative_templates.FIELDS[key]
            value = (existing["contents"].get(key, "") if existing else "")
            form_fields.append(
                '<div class="field"><label>' + esc(label).upper() + '</label>'
                '<input type="text" maxlength="180" name="field_' + esc(key)
                + '" value="' + esc(value) + '" placeholder="Enter ' + esc(label)
                + '"></div>'
            )
        form_route = "/admin/templates/record_update" if existing else "/admin/templates/record"
        form = (
            '<form method="post" action="' + form_route + '">'
            '<input type="hidden" name="csrf" value="' + esc(token) + '">'
            '<input type="hidden" name="name" value="' + esc(name) + '">'
            + ('<input type="hidden" name="id" value="' + str(existing["id"]) + '">'
               if existing else '')
            + '<div class="form-row">' + "".join(form_fields) + '</div>'
            '<div class="form-actions"><button type="submit">'
            + admin_ui.icon("check", 15)
            + (' Save record changes' if existing else ' Add content record')
            + '</button>'
            + ('<a class="btn btn-secondary" href="/admin/templates/rows?name='
               + quote(name) + '">Cancel edit</a>' if existing else '')
            + '</div></form>'
        )
        table_rows = []
        for item in items:
            rec_id = str(item["id"])
            content = item["contents"]
            preview_text = " · ".join(
                creative_templates.FIELDS.get(field, field) + ": " + str(value)[:45]
                for field, value in content.items()
            )
            table_rows.append(
                '<tr><td class="name-cell">#' + rec_id + '</td>'
                '<td><span class="badge green">Saved</span></td>'
                '<td title="' + esc(preview_text) + '">'
                + esc(preview_text[:145] or "Empty content") + '</td>'
                '<td><div class="actions">'
                '<a class="btn btn-secondary" target="_blank" rel="noreferrer" '
                'href="/admin/templates/view?name=' + quote(name) + '&id=' + rec_id
                + '">' + admin_ui.icon("image", 14) + ' Preview</a>'
                '<a class="btn btn-secondary" title="Download SVG" '
                'href="/admin/templates/render?name=' + quote(name) + '&id=' + rec_id
                + '">' + admin_ui.icon("download", 14) + '</a>'
                '<a class="btn btn-secondary" title="Edit content" '
                'href="/admin/templates/rows?name=' + quote(name) + '&edit=' + rec_id
                + '">' + admin_ui.icon("edit", 14) + '</a>'
                '<form method="post" action="/admin/templates/record_delete" '
                'class="inline" data-confirm="Delete this data record permanently?">'
                '<input type="hidden" name="csrf" value="' + esc(token) + '">'
                '<input type="hidden" name="name" value="' + esc(name) + '">'
                '<input type="hidden" name="id" value="' + rec_id + '">'
                '<button type="submit" class="btn btn-danger" '
                'title="Delete record">' + admin_ui.icon("trash", 14)
                + '</button></form></div></td></tr>'
            )
        body = (
            '<div class="heading-row"><div><div class="eyebrow">CONTENT STUDIO</div>'
            '<h1>Database-driven versions</h1>'
            '<p>Create, edit and export different versions of your SVG artwork, '
            'using your own structured content.</p></div>'
            '<div class="heading-actions">'
            '<a class="btn btn-secondary" href="/admin/templates/edit?name='
            + quote(name) + '">' + admin_ui.icon("edit", 15) + ' Field mapping</a>'
            '<a class="btn btn-secondary" href="/admin/templates/csv?name='
            + quote(name) + '">' + admin_ui.icon("download", 15) + ' Export CSV</a>'
            '</div></div>'
            '<section class="panel" style="margin-bottom:20px">'
            '<div class="panel-head"><div><h2>'
            + ('Edit record #' + str(existing["id"]) if existing else 'Add a content version')
            + '</h2><p>Template: ' + esc(name)
            + '</p></div><span class="badge purple">' + str(len(keys))
            + ' mapped fields</span></div>'
            + form + '</section>'
            '<section class="panel"><div class="panel-head"><div>'
            '<h2>Saved versions</h2><p>Up to 100 most recent content records</p>'
            '</div><span class="badge">' + str(len(items)) + ' shown</span></div>'
            '<div class="table-scroll"><table class="data-table"><thead><tr>'
            '<th>Record</th><th>Status</th><th>Content preview</th><th>Actions</th>'
            '</tr></thead><tbody>'
            + ("".join(table_rows) if table_rows else
               '<tr><td colspan="4"><p>No records yet. Add the first record above.</p></td></tr>')
            + '</tbody></table></div></section>'
        )
        handler._send(200, _page("Content versions", body, active="records"))
    except Exception as exc:
        error(handler, exc)


def _export_csv(name):
    fields = creative_templates.saved_fields(name)
    if not fields:
        raise ValueError("Template mapping required before CSV export")
    items = creative_templates.get_rows(name, 100)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["record_id"] + fields)
    for item in items:
        values = []
        for field in fields:
            value = str(item["contents"].get(field, ""))
            # Prevent spreadsheet formula injection when exported content is opened.
            if value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            values.append(value)
        writer.writerow([item["id"]] + values)
    return buffer.getvalue().encode("utf-8-sig")


def do_get(handler, route, session):
    path = route.path
    params = parse_qs(route.query)
    name = (params.get("name") or [""])[0]
    if path == "/admin/templates/edit":
        editor(handler, session, name)
        return True
    if path == "/admin/templates/rows":
        rows(handler, session, name, (params.get("edit") or [None])[0])
        return True
    if path in ("/admin/templates/artwork", "/admin/templates/render",
                "/admin/templates/view", "/admin/templates/csv"):
        try:
            if path.endswith("/artwork"):
                data = creative_templates.pristine_preview(name)
                handler._send(200, data, "image/svg+xml; charset=utf-8")
            elif path.endswith("/csv"):
                data = _export_csv(name)
                handler._send(200, data, "text/csv; charset=utf-8", {
                    "Content-Disposition": "attachment; filename*=UTF-8''"
                    + quote("content-" + name.replace(".svg", "") + ".csv")
                })
            else:
                row_id = (params.get("id") or [None])[0]
                data = creative_templates.render(name, row_id)
                headers = None if path.endswith("/view") else {
                    "Content-Disposition": "attachment; filename*=UTF-8''"
                    + quote("generated-" + name)
                }
                handler._send(200, data, "image/svg+xml; charset=utf-8", headers)
        except Exception as exc:
            error(handler, exc)
        return True
    return False


def do_post(handler, path, fields):
    if path not in (
        "/admin/templates/map", "/admin/templates/record",
        "/admin/templates/record_update", "/admin/templates/record_delete",
    ):
        return False
    try:
        name = fields.get("name", "")
        if path.endswith("/map"):
            selections = {
                key[6:]: value for key, value in fields.items()
                if key.startswith("layer_") and value
            }
            creative_templates.save_mapping(
                name, fields.get("checksum", ""), selections
            )
            handler._redirect("/admin/templates/rows?name=" + quote(name))
        elif path.endswith("/record_delete"):
            creative_templates.delete_row(name, fields.get("id", ""))
            handler._redirect("/admin/templates/rows?name=" + quote(name))
        else:
            values = {
                key[6:]: value for key, value in fields.items()
                if key.startswith("field_")
            }
            if path.endswith("/record_update"):
                creative_templates.update_row(name, fields.get("id", ""), values)
            else:
                creative_templates.add_row(name, values)
            handler._redirect("/admin/templates/rows?name=" + quote(name))
    except Exception as exc:
        error(handler, exc)
    return True
