"""Persistent, privacy-minimal tracking for submitted request metadata.

The verification URL itself and identity documents are never stored.
"""
import os
import sqlite3
import threading
from datetime import datetime, timezone

_LOCK = threading.RLock()


def _path():
    folder = os.getenv("PPYXR_DATA_DIR") or os.getenv("DATA_DIR") or "/data"
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "ppy xr_requests.sqlite3".replace(" ", ""))


def _db():
    db = sqlite3.connect(_path(), timeout=20)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    with _LOCK:
        with _db() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    link_count INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'awaiting_official_verification',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS requests_chat_idx ON requests(chat_id, id)"
            )


def submit(chat_id, link_count):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _LOCK:
        with _db() as conn:
            cursor = conn.execute(
                """INSERT INTO requests (chat_id, link_count, status, created_at, updated_at)
                VALUES (?, ?, 'awaiting_official_verification', ?, ?)""",
                (int(chat_id), int(link_count), now, now),
            )
            return cursor.lastrowid


def get_for_user(chat_id, request_id):
    with _LOCK:
        with _db() as conn:
            item = conn.execute(
                "SELECT id, link_count, status, created_at FROM requests WHERE chat_id=? AND id=?",
                (int(chat_id), int(request_id)),
            ).fetchone()
    return dict(item) if item else None


def recent_for_user(chat_id, limit=10):
    with _LOCK:
        with _db() as conn:
            rows = conn.execute(
                """SELECT id, link_count, status, created_at
                FROM requests WHERE chat_id=? ORDER BY id DESC LIMIT ?""",
                (int(chat_id), min(max(int(limit), 1), 20)),
            ).fetchall()
    return [dict(row) for row in rows]
