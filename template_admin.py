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

import creative_admin
import creative_templates
import admin_ui
import admin_dashboard
import raster_admin
import raster_ui
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


def _page(title, inner, active="dashboard"):
    return admin_ui.page(title, inner, active)



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
            "default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self'; form-action 'self'; "
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
                max_num_fields=120,
            ).items()}
        except (UnicodeError, ValueError):
            return {}

    def _login_page(self, message=""):
        login_nonce = _new_session(_admin_key())
        warning = (
            '<div class="note error">' + html.escape(message) + '</div>'
            if message else ""
        )
        body = (
            '<div class="eyebrow">WELCOME BACK</div>'
            '<h1>Sign in to your<br>creative workspace.</h1>'
            '<p style="margin-top:14px">Your designs, content and tools, all in one private dashboard.</p>'
            '<section class="card">' + warning
            + '<form method="post" action="/admin/templates/login">'
            '<input type="hidden" name="login_nonce" value="'
            + html.escape(login_nonce, quote=True) + '">'
            '<div class="field"><label for="admin-username">USERNAME</label>'
            '<input id="admin-username" type="text" name="username" '
            'required autocomplete="username" placeholder="Enter admin username"></div>'
            '<div class="field"><label for="admin-password">PASSWORD</label>'
            '<input id="admin-password" type="password" name="password" '
            'required autocomplete="current-password" placeholder="Enter your password"></div>'
            '<button type="submit">' + admin_ui.icon("shield", 17)
            + ' Access dashboard ' + admin_ui.icon("arrow", 17)
            + '</button></form><p style="font-size:11px;margin-top:20px">'
            'Access is restricted to authorized workspace administrators.</p></section>'
        )
        self._send(200, _page("Login", body, active="login"))

    def _dashboard(self, session, message="", view="dashboard"):
        return admin_dashboard.render(self, session, message, view)

    def do_GET(self):
        route = urlsplit(self.path)
        if route.path == "/health":
            self._send(200, b"ok\n", "text/plain; charset=utf-8")
            return
        if route.path == "/admin/assets/styles.css":
            self._send(200, admin_ui.STYLE.encode("utf-8"), "text/css; charset=utf-8")
            return
        if route.path == "/admin/assets/raster.css":
            self._send(200, raster_ui.STYLE.encode("utf-8"), "text/css; charset=utf-8")
            return
        if route.path == "/admin/assets/raster.js":
            self._send(200, raster_ui.SCRIPT.encode("utf-8"), "text/javascript; charset=utf-8")
            return
        if route.path == "/admin/assets/app.js":
            self._send(200, admin_ui.SCRIPT.encode("utf-8"), "text/javascript; charset=utf-8")
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
            self._dashboard(
                session,
                (params.get("msg") or [""])[0],
                (params.get("view") or ["dashboard"])[0],
            )
            return
        if route.path == "/admin/templates/thumb":
            name = (parse_qs(route.query).get("name") or [""])[0]
            if not _valid_name(name):
                self._send(400, b"Invalid file name", "text/plain")
                return
            suffix = Path(name).suffix.lower()
            types = {".png": "image/png", ".jpg": "image/jpeg",
                     ".jpeg": "image/jpeg", ".webp": "image/webp"}
            path = _folder() / name
            if suffix not in types or path.is_symlink() or not path.is_file():
                self._send(404, b"Preview not available", "text/plain")
                return
            self._send(200, path.read_bytes(), types[suffix])
            return
        if raster_admin.do_get(self, route, session):
            return
        if creative_admin.do_get(self, route, session):
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
            "/admin/templates/map", "/admin/templates/record",
            "/admin/templates/record_update", "/admin/templates/record_delete",
            "/admin/templates/raster/save", "/admin/templates/raster/add_record",
            "/admin/templates/raster/update_record",
            "/admin/templates/raster/delete_record",
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
                if name.lower().endswith(".svg"):
                    self._redirect("/admin/templates/edit?name=" + quote(name))
                elif Path(name).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    self._redirect("/admin/templates/raster/edit?name=" + quote(name))
                else:
                    self._redirect("/admin/templates?msg=Template+saved+successfully")
                return
            except Exception as exc:
                LOG.warning("Template upload failed: %s", type(exc).__name__)
                self._send(400, _page("Upload failed",
                    '<div class="note error">Unable to process upload.</div>'
                    '<a href="/admin/templates">Back to templates</a>'))
                return
        if raster_admin.do_post_json(self, route, body, _csrf(key, session)):
            return
        fields = self._fields(body)
        if not hmac.compare_digest(fields.get("csrf", ""), _csrf(key, session)):
            self._send(403, b"Invalid form token", "text/plain")
            return
        if raster_admin.do_post_form(self, route, fields):
            return
        if creative_admin.do_post(self, route, fields):
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
