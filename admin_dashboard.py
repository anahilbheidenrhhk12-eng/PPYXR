"""Digi Pro Studio: dashboard, template library, upload and settings views."""
import html
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import admin_ui
import creative_templates
import raster_creatives


def esc(value):
    return html.escape(str(value), quote=True)


def item_icon(kind):
    return admin_ui.icon("image" if kind in ("PNG", "JPG", "JPEG", "WEBP", "SVG") else "file", 32)


def overview_data():
    from template_admin import _folder, _valid_name
    files = [
        item for item in _folder().iterdir()
        if item.is_file() and not item.is_symlink() and _valid_name(item.name)
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        details = creative_templates.overview()
        db_online = True
    except Exception:
        details = {"mappings": {}, "counts": {}, "records": 0, "recent": []}
        db_online = False
    try:
        details["raster"] = raster_creatives.overview()
    except Exception:
        details["raster"] = {"mappings": {}, "counts": {}, "records": 0}
    return files, details, db_online


def stats(files, detail, db_online):
    image_types = {".jpg", ".jpeg", ".png", ".webp"}
    editable = sum(1 for f in files if f.suffix.lower() in image_types)
    raster = detail.get("raster", {"mappings": {}, "counts": {}, "records": 0})
    mapped_svg = sum(1 for f in files if f.suffix.lower() == ".svg" and f.name in detail["mappings"])
    mapped_raster = sum(1 for f in files if f.suffix.lower() in image_types and f.name in raster["mappings"])
    blocks = [
        ("Total templates", len(files), "layers", "All uploaded design assets"),
        ("Visual images", editable, "image", "PNG / JPG / WEBP available"),
        ("Mapped templates", mapped_svg + mapped_raster if db_online else "—", "bolt", "Configured field sets"),
        ("Content records", detail["records"] + raster["records"] if db_online else "—",
         "database", "Saved in PostgreSQL"),
    ]
    return '<div class="stats-grid">' + "".join(
        '<article class="stat-card"><div class="stat-top"><span>' + label
        + '</span><span class="stat-icon">' + admin_ui.icon(glyph, 17)
        + '</span></div><div class="stat-value">' + str(value)
        + '</div><div class="stat-footer">' + note + '</div></article>'
        for label, value, glyph, note in blocks
    ) + '</div>'


def template_card(path, detail):
    from template_admin import _friendly_size, _csrf, _admin_key
    # csrf belongs to the session, so this markup is wrapped by cards().
    raise NotImplementedError


def cards(files, detail, token):
    if not files:
        return (
            '<div class="empty-state">' + admin_ui.icon("layers", 35)
            + '<strong>No templates uploaded yet</strong>'
            '<p>Your creative workspace is ready. Upload your first design '
            'to start organizing and mapping its fields.</p>'
            '<a class="btn" style="margin-top:16px" '
            'href="/admin/templates?view=upload">+ Add first template</a></div>'
        )
    results = []
    mapped = detail["mappings"]
    record_counts = detail["counts"]
    raster_mapped = detail.get("raster", {}).get("mappings", {})
    raster_counts = detail.get("raster", {}).get("counts", {})
    for path in files:
        name = path.name
        slug = quote(name)
        safe_name = esc(name)
        stat = path.stat()
        kind = path.suffix.lstrip(".").upper()
        is_svg = kind == "SVG"
        is_image = is_svg or kind in ("PNG", "JPG", "JPEG", "WEBP")
        src = ("/admin/templates/artwork?name=" if is_svg else
               "/admin/templates/thumb?name=") + slug
        art = ('<img alt="" loading="lazy" src="' + esc(src) + '">' if is_image
               else '<span class="format-icon">' + item_icon(kind) + '</span>')
        editable_raster = kind in ("PNG", "JPG", "JPEG", "WEBP")
        configured_svg = is_svg and name in mapped
        configured_raster = editable_raster and name in raster_mapped
        configured = configured_svg or configured_raster
        status = ('<span class="badge green">' + admin_ui.icon("check", 12)
                  + ' Configured</span>' if configured else
                  '<span class="badge warning">Needs mapping</span>'
                  if is_svg or editable_raster else
                  '<span class="badge">Stored file</span>')
        time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%d %b %Y")
        primary = (
            '<a class="btn" href="/admin/templates/edit?name=' + slug + '">'
            + admin_ui.icon("edit", 14) + ' Edit fields</a>'
            if is_svg else ''
        )
        if editable_raster:
            primary = (
                '<a class="btn" href="/admin/templates/raster/edit?name='
                + slug + '">' + admin_ui.icon("edit", 14) + ' Visual editor</a>'
            )
        if configured:
            record_path = (
                "/admin/templates/rows?name=" if is_svg else
                "/admin/templates/raster/records?name="
            )
            primary += (
                '<a class="btn btn-secondary" href="' + record_path
                + slug + '">' + admin_ui.icon("database", 14) + ' Content</a>'
            )
        if not primary:
            primary = (
                '<a class="btn btn-secondary" href="/admin/templates/file?name='
                + slug + '">' + admin_ui.icon("download", 14) + ' Download</a>'
            )
        results.append(
            '<article class="template-card" data-template-card'
            ' data-name="' + safe_name + '" data-type="' + esc(kind.lower()) + '"'
            ' data-modified="' + str(int(stat.st_mtime)) + '"'
            ' data-size="' + str(stat.st_size) + '">'
            '<div class="template-art">' + art
            + '<span class="format-label">' + esc(kind) + '</span></div>'
            '<div class="template-content"><strong class="template-name" title="'
            + safe_name + '">' + safe_name + '</strong>'
            '<div class="template-meta"><span>' + time + '</span><span class="dot"></span>'
            '<span>' + _size(stat.st_size) + '</span></div>'
            '<div style="margin-bottom:15px;display:flex;gap:6px;align-items:center;flex-wrap:wrap">'
            + status +
            ('<span class="badge">' + str((record_counts if is_svg else raster_counts).get(name, 0)) + ' versions</span>'
             if configured else '')
            + '</div><div class="template-actions">' + primary +
            '<a class="btn btn-ghost" title="Download original" '
            'href="/admin/templates/file?name=' + slug + '">'
            + admin_ui.icon("download", 14) + '</a>'
            '<form class="inline" method="post" action="/admin/templates/delete" '
            'data-confirm="Delete this template from the library? Its file will be removed.">'
            '<input type="hidden" name="csrf" value="' + esc(token) + '">'
            '<input type="hidden" name="name" value="' + safe_name + '">'
            '<button type="submit" class="btn btn-danger" title="Delete file">'
            + admin_ui.icon("trash", 14) + '</button></form>'
            '</div></div></article>'
        )
    return "".join(results)


def _size(number):
    return (("%.1f MB" % (number / 1024 / 1024))
            if number >= 1024*1024 else ("%.1f KB" % (number / 1024)))


def gallery(files, detail, token, limit=None, controls=True):
    selected = files[:limit] if limit else files
    htmltext = ""
    if controls:
        htmltext += (
            '<div class="control-row">'
            '<div class="searchbox">' + admin_ui.icon("search", 17)
            + '<input type="text" data-search aria-label="Search templates" '
            'placeholder="Search templates by name..." autocomplete="off"></div>'
            '<select class="select-small" data-filter aria-label="Filter file type">'
            '<option value="all">All formats</option>'
            '<option value="svg">SVG</option><option value="png">PNG</option>'
            '<option value="jpg">JPG</option><option value="jpeg">JPEG</option>'
            '<option value="webp">WEBP</option><option value="pdf">PDF</option>'
            '<option value="docx">DOCX</option><option value="zip">ZIP</option>'
            '</select>'
            '<select class="select-small" data-sort aria-label="Sort templates">'
            '<option value="recent">Newest first</option>'
            '<option value="name">Name A–Z</option>'
            '<option value="size">Largest files</option></select>'
            '<button class="toolbar-button" type="button" data-view-toggle '
            'aria-label="Toggle grid and list" aria-pressed="false">'
            + admin_ui.icon("layers", 17) + ' View</button></div>'
        )
    htmltext += '<div class="template-grid" data-template-grid>' + cards(selected, detail, token) + '</div>'
    if selected:
        htmltext += ('<div class="empty-state" data-search-empty style="display:none">'
                     '<strong>No matching templates</strong>'
                     '<p>Try another search term or file type.</p></div>')
    return htmltext


def upload_form(token):
    return (
        '<form method="post" action="/admin/templates/upload" '
        'enctype="multipart/form-data">'
        '<div class="dropzone" data-dropzone role="button" tabindex="0">'
        '<span class="drop-icon">' + admin_ui.icon("upload", 26) + '</span>'
        '<strong>Drop your creative file here</strong>'
        '<p>Drag a file into this area, or click to browse your computer</p>'
        '<span class="badge purple">Browse files</span>'
        '<input type="file" name="file" required aria-label="Select template" '
        'accept=".svg,.png,.jpg,.jpeg,.webp,.pdf,.zip,.docx">'
        '<span class="file-name" data-filename>Maximum file size: 20 MB</span></div>'
        '<input type="hidden" name="csrf" value="' + esc(token) + '">'
        '<div class="form-actions" style="justify-content:space-between">'
        '<label class="checkline"><input type="checkbox" name="replace" value="yes"> '
        'Replace file when the filename already exists</label>'
        '<button type="submit">' + admin_ui.icon("upload", 16) + ' Upload template</button>'
        '</div></form>'
    )


def heading(eyebrow, title, subtitle, buttons=""):
    return (
        '<div class="heading-row"><div><div class="eyebrow">' + eyebrow + '</div>'
        '<h1>' + title + '</h1><p>' + subtitle + '</p></div>'
        + ('<div class="heading-actions">' + buttons + '</div>' if buttons else '') + '</div>'
    )


def dashboard_view(files, data, db_online, token):
    blocks = [
        ("Upload a file", "Build your template library", "upload",
         "/admin/templates?view=upload"),
        ("Map fields", "Choose regions or editable SVG text layers", "edit",
         "/admin/templates?view=library"),
        ("Manage data", "Generate versions with PostgreSQL", "database",
         "/admin/templates?view=records"),
    ]
    quick = "".join(
        '<a class="quick-item" href="' + url + '"><span>' + admin_ui.icon(ic, 22)
        + '</span><span><strong>' + name + '</strong><small>' + note
        + '</small></span></a>'
        for name, note, ic, url in blocks
    )
    steps = [
        ("01", "Upload", "Add an SVG exported with editable text layers."),
        ("02", "Configure", "Map SVG text or draw text regions on an image."),
        ("03", "Generate", "Add marketing content records and export new designs."),
    ]
    guide = "".join(
        '<div class="mini-step"><span class="step-num">' + n + '</span>'
        '<div><strong>' + title + '</strong><p>' + text
        + '</p></div></div>' for n, title, text in steps
    )
    body = (
        heading(
            "CONTROL CENTER", "Creative workspace <em>overview</em>",
            "Manage your assets, prepare editable designs and generate consistent "
            "promotional artwork from structured content.",
            '<a class="btn btn-secondary" href="/admin/templates?view=library">'
            + admin_ui.icon("layers", 16) + ' Template library</a>'
            '<a class="btn" href="/admin/templates?view=upload">'
            + admin_ui.icon("plus", 16) + ' Add new template</a>'
        )
        + stats(files, data, db_online)
        + '<div class="two-columns"><section class="panel">'
        '<div class="panel-head"><div><h2>Quick actions</h2>'
        '<p>Everything needed to manage your creative workflow</p></div></div>'
        '<div class="quick-grid">' + quick + '</div></section>'
        '<section class="panel"><div class="panel-head"><div><h2>How it works</h2>'
        '<p>Three steps to produce a new version</p></div></div>'
        '<div class="mini-steps">' + guide + '</div></section></div>'
        '<div class="section-header"><div><h2>Recent templates</h2>'
        '<p>Your newest uploaded creative files</p></div>'
        '<a class="btn btn-secondary" href="/admin/templates?view=library">'
        'View all templates ' + admin_ui.icon("arrow", 14) + '</a></div>'
        + gallery(files, data, token, limit=6, controls=False)
    )
    return body


def library_view(files, data, token):
    return (
        heading(
            "ASSET MANAGEMENT", "Template library",
            "Browse, inspect and organize all uploaded artwork and documents.",
            '<a class="btn" href="/admin/templates?view=upload">'
            + admin_ui.icon("plus", 16) + ' Upload template</a>',
        )
        + gallery(files, data, token, controls=True)
    )


def upload_view(token):
    checks = [
        ("SVG", "Editable text-field mapping and version generation"),
        ("PNG / JPG / WEBP", "Visual text editor, smart placement and version generation"),
        ("PDF / DOCX", "File storage and download"),
        ("ZIP", "Archive storage and download"),
    ]
    formats = "".join(
        '<div class="setting"><div><strong>' + fmt
        + '</strong><small>' + desc + '</small></div>'
        '<span class="badge">' + admin_ui.icon("check", 12) + '</span></div>'
        for fmt, desc in checks
    )
    body = (
        heading(
            "ASSET UPLOAD", "Upload center",
            "Upload editable SVG artwork or a regular image for the visual editor.",
            '<a class="btn btn-secondary" href="/admin/templates?view=library">'
            + admin_ui.icon("layers", 16) + ' View library</a>',
        )
        + '<div class="two-columns"><section class="panel">'
        '<div class="panel-head"><div><h2>Add a new file</h2>'
        '<p>Uploads are stored on the project persistent volume</p></div></div>'
        + upload_form(token)
        + '</section><section class="panel"><div class="panel-head"><div>'
        '<h2>Supported formats</h2><p>Choose the right type for your task</p>'
        '</div></div>' + formats + '</section></div>'
        '<div class="note">' + admin_ui.icon("info", 15)
        + ' SVG files preserve native text layers. PNG, JPG and WEBP open in the '
        'interactive visual editor for new promotional text regions.</div>'
    )
    return body


def records_view(files, data, db_online):
    count = data["counts"]
    mappings = data["mappings"]
    entries = []
    for name, mapping in sorted(mappings.items(), key=lambda item: item[0].lower()):
        if not any(file.name == name for file in files):
            continue
        fields = mapping.get("layer_map") or {}
        entries.append(
            '<tr><td class="name-cell">' + esc(name) + '</td>'
            '<td><span class="badge purple">' + str(len(fields)) + ' text layers</span></td>'
            '<td>' + str(count.get(name, 0)) + '</td>'
            '<td><a class="btn btn-secondary" href="/admin/templates/rows?name='
            + quote(name) + '">Manage records ' + admin_ui.icon("arrow", 13)
            + '</a></td></tr>'
        )
    raster = data.get("raster", {"mappings": {}, "counts": {}})
    for name, config in sorted(raster["mappings"].items(), key=lambda item: item[0].lower()):
        if not any(file.name == name for file in files):
            continue
        layers = config.get("overlays") or []
        entries.append(
            '<tr><td class="name-cell">' + esc(name) + '</td>'
            '<td><span class="badge purple">' + str(len(layers)) + ' text regions</span></td>'
            '<td>' + str(raster["counts"].get(name, 0)) + '</td>'
            '<td><a class="btn btn-secondary" href="/admin/templates/raster/records?name='
            + quote(name) + '">Manage records ' + admin_ui.icon("arrow", 13)
            + '</a></td></tr>'
        )
    body = heading(
        "STRUCTURED CONTENT", "Content records",
        "Select a configured template to create, review or download its versions.",
        '<a class="btn" href="/admin/templates?view=library">'
        + admin_ui.icon("layers", 16) + ' Configure templates</a>',
    )
    if not db_online:
        body += '<div class="note error">Database is temporarily unavailable. Existing files are safe.</div>'
    body += (
        '<section class="panel"><div class="panel-head"><div><h2>Connected templates</h2>'
        '<p>Field mappings and record counts from PostgreSQL</p></div>'
        '<span class="badge green">' + str(len(entries)) + ' connected</span></div>'
        '<div class="table-scroll"><table class="data-table"><thead><tr>'
        '<th>Template</th><th>Mapped layers</th><th>Records</th><th>Actions</th></tr>'
        '</thead><tbody>'
        + ("".join(entries) or '<tr><td colspan="4"><p class="muted">'
           'No mapped templates found. Open a visual image editor or SVG field editor.'
           '</p></td></tr>')
        + '</tbody></table></div></section>'
    )
    return body


def settings_view(token, files, db_online):
    from template_admin import _folder, ALLOWED, MAX_UPLOAD
    entries = [
        ("Workspace", "DIGI PRO · PPYXR", "Private administration"),
        ("Database", "PostgreSQL" if db_online else "Connection unavailable",
         "Creative mappings and content records"),
        ("Storage", "/data/templates", "Railway persistent volume"),
        ("Maximum upload", str(MAX_UPLOAD//(1024*1024)) + " MB", "Single-file upload limit"),
        ("Accepted formats", ", ".join(sorted(ALLOWED)), "Stored asset formats"),
        ("Editable formats", "SVG, PNG, JPG, WEBP", "Text mapping, visual overlays and rendering"),
    ]
    rows = "".join(
        '<div class="setting"><div><strong>' + esc(title)
        + '</strong><small>' + esc(description)
        + '</small></div><code>' + esc(value) + '</code></div>'
        for title, value, description in entries
    )
    return (
        heading("WORKSPACE ADMIN", "Settings & access",
                "See your environment configuration, preferences and account controls.")
        + '<div class="settings-grid"><section class="panel">'
        '<div class="panel-head"><div><h2>System configuration</h2>'
        '<p>Live capabilities of this workspace</p></div></div>'
        + rows + '</section><section class="panel">'
        '<div class="panel-head"><div><h2>Security & access</h2>'
        '<p>Administrator-only controls</p></div></div>'
        '<div class="note">' + admin_ui.icon("shield", 15)
        + ' The template manager requires admin authentication. '
        'Uploaded files are not publicly listed.</div>'
        '<div class="setting"><div><strong>Administrator credentials</strong>'
        '<small>Manage ADMIN_USER and ADMIN_PASSWORD on Railway</small></div>'
        '<a class="btn btn-ghost" href="https://railway.com/project/e9d634f1-76b1-4b2f-8595-aa44f22cfa82" '
        'target="_blank" rel="noreferrer noopener">Railway ' + admin_ui.icon("external", 14)
        + '</a></div>'
        '<div class="setting"><div><strong>Appearance</strong>'
        '<small>Use the sun icon at the top to switch themes</small></div>'
        '<span class="badge">Dark / Light</span></div>'
        '<div style="margin-top:24px"><form method="post" action="/admin/templates/logout">'
        '<input type="hidden" name="csrf" value="' + esc(token) + '">'
        '<button class="ghost" type="submit">' + admin_ui.icon("logout", 15)
        + ' Sign out of this workspace</button></form></div></section></div>'
    )


def render(handler, session, message="", view="dashboard"):
    from template_admin import _admin_key, _csrf, _page
    view = view if view in ("dashboard", "library", "upload", "records", "settings") else "dashboard"
    files, details, db_online = overview_data()
    token = _csrf(_admin_key(), session)
    pages = {
        "dashboard": ("Overview", lambda: dashboard_view(files, details, db_online, token)),
        "library": ("Template library", lambda: library_view(files, details, token)),
        "upload": ("Upload center", lambda: upload_view(token)),
        "records": ("Content records", lambda: records_view(files, details, db_online)),
        "settings": ("Settings", lambda: settings_view(token, files, db_online)),
    }
    title, builder = pages[view]
    body = builder()
    if message:
        body = '<div class="note success">' + esc(message[:180]) + '</div>' + body
    handler._send(200, _page(title, body, active=view))
