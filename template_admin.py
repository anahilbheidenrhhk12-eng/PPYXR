"""Password-protected template file manager for the Railway bot service.

This is a separate admin file library. Uploaded files are never executed,
rendered inline, or used in verification workflows automatically.
"""
import hashlib
import hmac
import html
import logging
import os
import secrets
import tempfile
import time
import unicodedata
from email import policy
from email.parser import BytesParser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

LOG = logging.getLogger("PPYXR.templates")
MAX_UPLOAD = 20 * 1024 * 1024
MAX_BODY = MAX_UPLOAD + 128 * 1024
ALLOWED = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".pdf", ".zip", ".docx"}
COOKIE_NAME = "ppy xr_admin".replace(" ", "")
SESSION_SECONDS = 8 * 60 * 60


def _folder():
    path = Path(os.getenv("TEMPLATE_STORAGE_DIR", "/data/templates"))
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def _admin_key():
    password = os.getenv("ADMIN_PASSWORD", "")
    extra = os.getenv("SESSION_SECRET", "")
    if not password or not os.getenv("ADMIN_USER", ""):
        return None
    return hashlib.sha256((password + ":" + extra).encode("utf-8")).digest()


def _valid_name(name):
    if not isinstance(name, str):
        return False
    name = unicodedata.normalize("NFC", name)
    if not (1 <= len(name) <= 120) or name[0] == ".":
        return False
    if any(not (c.isalnum() or c in " ._-()") for c in name):
        return False
    return Path(name).suffix.lower() in ALLOWED


def _sign(key, data):
    return hmac.new(key, data.encode("utf-8"), hashlib.sha256).hexdigest()


def _new_session(key):
    stamp = str(int(time.time()))
    base = stamp + "." + secrets.token_hex(16)
    return base + "." + _sign(key, base)


def _session_valid(key, value):
    try:
        stamp, nonce, signature = value.split(".")
        age = time.time() - int(stamp)
        return (0 <= age <= SESSION_SECONDS
                and len(nonce) == 32 and len(signature) == 64
                and hmac.compare_digest(_sign(key, stamp + "." + nonce), signature))
    except (TypeError, ValueError, AttributeError):
        return False


def _csrf(key, session):
    return _sign(key, "csrf:" + session)


def _page(title, inner):
    return ("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PPYXR · """ + html.escape(title) + """</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,Segoe UI,sans-serif}
*{box-sizing:border-box}body{margin:0;background:#0c1020;color:#e8ecf7}
main{max-width:920px;margin:32px auto;padding:0 18px}
h1{font-size:25px;margin:0 0 7px}h2{font-size:17px}
small,.muted{color:#94a0b8}.top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.card{background:#171f33;border:1px solid #2d3b57;border-radius:16px;padding:22px;margin:18px 0}
input[type=text],input[type=password],input[type=file]{display:block;width:100%;
background:#0e1528;border:1px solid #44516a;color:#fff;padding:12px;border-radius:9px;margin:8px 0 16px}
label{display:block;font-size:14px;font-weight:600}
button,.btn{background:#526af4;color:#fff;border:0;padding:10px 16px;border-radius:9px;
cursor:pointer;font-weight:650;text-decoration:none;display:inline-block}
button.danger{background:#943549}button.ghost{background:#303a55}
.row{display:flex;align-items:center;justify-content:space-between;gap:16px;
border-bottom:1px solid #2b3550;padding:12px 0;flex-wrap:wrap}
.row:last-child{border-bottom:0}.actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.note{padding:12px 14px;border-radius:10px;background:#26324e;color:#d9e4f9;margin:14px 0}
.error{background:#592937}.success{background:#254838}
a{color:#a5baff}form.inline{display:inline}code{color:#d4e4ff}
</style></head><body><main>""" + inner + "</main></body></html>").encode("utf-8")


def _friendly_size(n):
    return f"{n / (1024 * 1024):.1f} MB" if n >= 1024 * 1024 else f"{n / 1024:.1f} KB"


class TemplateAdminHandler(BaseHTTPRequestHandler):
    server_version = "PPYXR/1.0"

    def log_message(self, fmt, *args):
        LOG.debug(fmt, *args)

    def _send(self, status, data, content_type="text/html; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; "
            "frame-ancestors 'none'; base-uri 'none'",
        )
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location, cookie=None):
        headers = {"Location": location}
        if cookie:
            headers["Set-Cookie"] = cookie
        self._send(303, b"", extra=headers)

    def _logged_in(self):
        key = _admin_key()
        if not key:
            return None
        try:
            jar = SimpleCookie()
            jar.load(self.headers.get("Cookie", ""))
            cookie = jar.get(COOKIE_NAME)
            session = cookie.value if cookie else None
        except Exception:
            return None
        return session if _session_valid(key, session) else None

    def _read_body(self, maximum=MAX_BODY):
        try:
            n = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            return None
        if n < 0 or n > maximum:
            return None
        return self.rfile.read(n)

    def _fields(self, body):
        try:
            return {k: v[0] for k, v in parse_qs(
                body.decode("utf-8"), keep_blank_values=True,
                max_num_fields=12,
            ).items()}
        except (UnicodeError, ValueError):
            return {}

    def _login_page(self, message=""):
        login_nonce = _new_session(_admin_key())
        warning = ('<div class="note error">' + html.escape(message) + '</div>') if message else ""
        body = ("""<div class="top"><div><h1>🔐 PPYXR Template Manager</h1>
<p class="muted">Private administrator access</p></div></div>
<section class="card">""" + warning + """
<form method="post" action="/admin/templates/login">
<input type="hidden" name="login_nonce" value="__LOGIN_NONCE__">
<label>Admin username</label><input type="text" name="username" required autocomplete="username">
<label>Admin password</label><input type="password" name="password" required autocomplete="current-password">
<button type="submit">Sign in</button></form>
<p class="muted"><small>Credentials: Railway → PIXEL → Variables → ADMIN_USER / ADMIN_PASSWORD.</small></p>
</section>""")
        body = body.replace("__LOGIN_NONCE__", html.escape(login_nonce, quote=True))
        self._send(200, _page("Login", body))

    def _dashboard(self, session, message=""):
        key = _admin_key()
        csrf = _csrf(key, session)
        files = []
        for path in _folder().iterdir():
            if path.is_file() and not path.is_symlink() and _valid_name(path.name):
                files.append(path)
        files.sort(key=lambda p: p.name.lower())
        items = []
        for path in files:
            name = html.escape(path.name, quote=True)
            link = "/admin/templates/file?name=" + quote(path.name)
            items.append(
                '<div class="row"><div><strong>' + name + '</strong>'
                '<div class="muted"><small>' + _friendly_size(path.stat().st_size) + '</small></div></div>'
                '<div class="actions"><a class="btn" href="' + html.escape(link, quote=True)
                + '">Download</a><form method="post" action="/admin/templates/delete" class="inline">'
                '<input type="hidden" name="csrf" value="' + csrf + '">'
                '<input type="hidden" name="name" value="' + name + '">'
                '<button type="submit" class="danger">Delete</button></form></div></div>'
            )
        alert = ""
        if message:
            alert = '<div class="note">' + html.escape(message[:180]) + '</div>'
        body = ("""<div class="top"><div><h1>📁 PPYXR Templates</h1>
<p class="muted">Private admin library · Stored on Railway persistent volume</p></div>
<form method="post" action="/admin/templates/logout">
<input type="hidden" name="csrf" value="%s"><button class="ghost">Log out</button></form></div>
%s
<section class="card"><h2>Upload or replace a template</h2>
<form action="/admin/templates/upload" method="post" enctype="multipart/form-data">
<input type="hidden" name="csrf" value="%s">
<label>Template file</label><input name="file" type="file"
accept=".svg,.png,.jpg,.jpeg,.webp,.pdf,.zip,.docx" required>
<label><input type="checkbox" name="replace" value="yes"> Replace existing file if names match</label>
<p class="muted"><small>Allowed: SVG, PNG, JPG, WEBP, PDF, ZIP, DOCX. Max 20 MB per file.</small></p>
<button type="submit">Upload template</button></form></section>
<section class="card"><h2>Saved templates (%d)</h2>%s</section>
<p class="muted"><small>Only files uploaded here are managed; no existing project files are changed.
This library does not automatically change eligibility-verification workflows.</small></p>"""
                % (csrf, alert, csrf, len(files), "".join(items) or '<p class="muted">No templates uploaded yet.</p>'))
        self._send(200, _page("Templates", body))

    def do_GET(self):
        route = urlsplit(self.path)
        if route.path == "/health":
            self._send(200, b"ok\n", "text/plain; charset=utf-8")
            return
        if route.path in ("/admin", "/admin/"):
            self._redirect("/admin/templates")
            return
        if not route.path.startswith("/admin/templates"):
            self._send(404, b"Not found", "text/plain")
            return
        if not _admin_key():
            self._send(503, _page("Setup required",
                '<h1>Admin login is not configured</h1><p>Set ADMIN_USER and ADMIN_PASSWORD in Railway → PIXEL → Variables.</p>'))
            return
        session = self._logged_in()
        if not session:
            self._login_page()
            return
        if route.path == "/admin/templates":
            params = parse_qs(route.query)
            self._dashboard(session, (params.get("msg") or [""])[0])
            return
        if route.path == "/admin/templates/file":
            name = (parse_qs(route.query).get("name") or [""])[0]
            if not _valid_name(name):
                self._send(400, b"Invalid file name", "text/plain")
                return
            path = _folder() / name
            if not path.is_file() or path.is_symlink():
                self._send(404, b"Not found", "text/plain")
                return
            data = path.read_bytes()
            self._send(200, data, "application/octet-stream", {
                "Content-Disposition": "attachment; filename*=UTF-8''" + quote(name)
            })
            return
        self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in (
            "/admin/templates/login", "/admin/templates/logout",
            "/admin/templates/upload", "/admin/templates/delete",
        ):
            self._send(404, b"Not found", "text/plain")
            return
        # Railway/browser proxy origin headers are not reliable. Each POST
        # is instead protected by a signed nonce or session-bound CSRF token.
        key = _admin_key()
        if not key:
            self._send(503, b"Admin credentials not configured", "text/plain")
            return
        if route == "/admin/templates/login":
            body = self._read_body(8192)
            if body is None:
                self._send(413, b"Request too large", "text/plain")
                return
            fields = self._fields(body)
            nonce = fields.get("login_nonce", "")
            if not _session_valid(key, nonce):
                self._login_page("Login page expired. Please sign in again.")
                return
            # A login token is valid for 15 minutes; mutations after login
            # remain protected by session-bound CSRF tokens.
            if time.time() - int(nonce.split(".", 1)[0]) > 900:
                self._login_page("Login page expired. Please sign in again.")
                return
            correct = hmac.compare_digest(fields.get("username", ""), os.getenv("ADMIN_USER", ""))
            correct &= hmac.compare_digest(fields.get("password", ""), os.getenv("ADMIN_PASSWORD", ""))
            if not correct:
                self._login_page("Invalid admin credentials.")
                return
            session = _new_session(key)
            cookie = (f"{COOKIE_NAME}={session}; Max-Age={SESSION_SECONDS}; "
                      "Path=/admin; HttpOnly; Secure; SameSite=Strict")
            self._redirect("/admin/templates", cookie)
            return

        session = self._logged_in()
        if not session:
            self._send(401, b"Login required", "text/plain")
            return
        body = self._read_body()
        if body is None:
            self._send(413, b"Invalid or oversized upload", "text/plain")
            return
        if route == "/admin/templates/upload":
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self._send(415, b"Expected multipart form", "text/plain")
                return
            try:
                wrapped = (
                    ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n")
                    .encode("utf-8") + body
                )
                message = BytesParser(policy=policy.default).parsebytes(wrapped)
                fields = {}
                payload = None
                name = None
                if not message.is_multipart():
                    raise ValueError("Invalid multipart request")
                for part in message.iter_parts():
                    field = part.get_param("name", header="content-disposition")
                    if field in ("csrf", "replace"):
                        fields[field] = part.get_payload(decode=True).decode("utf-8")
                    elif field == "file" and payload is None:
                        name = part.get_filename()
                        payload = part.get_payload(decode=True)
                if not hmac.compare_digest(fields.get("csrf", ""), _csrf(key, session)):
                    self._send(403, b"Invalid form token", "text/plain")
                    return
                if not _valid_name(name) or payload is None or len(payload) > MAX_UPLOAD:
                    self._send(400, _page("Upload error",
                        '<div class="note error">Invalid file name, extension, or file size.</div>'
                        '<a href="/admin/templates">Back to templates</a>'))
                    return
                path = _folder() / name
                if (path.exists() and fields.get("replace") != "yes") or path.is_symlink():
                    self._redirect("/admin/templates?msg=File+already+exists.+Check+replace+to+overwrite.")
                    return
                temp = None
                try:
                    with tempfile.NamedTemporaryFile(
                        mode="wb", prefix=".upload-", dir=_folder(), delete=False
                    ) as outfile:
                        temp = outfile.name
                        outfile.write(payload)
                    os.chmod(temp, 0o600)
                    os.replace(temp, path)
                finally:
                    if temp and os.path.exists(temp):
                        os.unlink(temp)
                LOG.info("Admin uploaded template %s (%d bytes)", name, len(payload))
                self._redirect("/admin/templates?msg=Template+saved+successfully")
                return
            except Exception as exc:
                LOG.warning("Template upload failed: %s", type(exc).__name__)
                self._send(400, _page("Upload failed",
                    '<div class="note error">Unable to process upload.</div>'
                    '<a href="/admin/templates">Back to templates</a>'))
                return
        fields = self._fields(body)
        if not hmac.compare_digest(fields.get("csrf", ""), _csrf(key, session)):
            self._send(403, b"Invalid form token", "text/plain")
            return
        if route == "/admin/templates/logout":
            self._redirect("/admin/templates", (
                f"{COOKIE_NAME}=; Max-Age=0; Path=/admin; HttpOnly; Secure; SameSite=Strict"
            ))
            return
        if route == "/admin/templates/delete":
            name = fields.get("name")
            if not _valid_name(name):
                self._send(400, b"Invalid file name", "text/plain")
                return
            path = _folder() / name
            if path.is_file() and not path.is_symlink():
                path.unlink()
                LOG.info("Admin deleted template %s", name)
            self._redirect("/admin/templates?msg=Template+deleted")
            return
