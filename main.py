"""PPYXR: safe Telegram support and official verification navigation service.

The original document-generation / automated eligibility-verification modules
are intentionally NOT imported by this entrypoint.
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("ppy xr".replace(" ", ""))

OFFICIAL_URL = "https://one.google.com/ai-student"


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health"):
            self.send_error(404)
            return
        payload = json.dumps({
            "service": "PPYXR",
            "status": "running",
            "automatic_verification": "disabled",
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        logger.debug("HTTP " + format, *args)


def serve_health():
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info("Health endpoint listening on port %s", port)
    server.serve_forever()


def official_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎓 Official Student Verification", url=OFFICIAL_URL),
    ]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "👋 Welcome to PPYXR!\n\n"
        "🎓 Student eligibility must be verified using the official service.\n"
        "Use the button below to open Google's student offer page.",
        reply_markup=official_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ PPYXR help\n\n"
        "1. Open the official student offer page.\n"
        "2. Follow the official eligibility and document instructions.\n"
        "3. Contact the official provider for verification decisions.\n\n"
        "Automatic verification is not enabled in this deployment.",
        reply_markup=official_keyboard(),
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "✅ PPYXR bot is online.\n"
        "ℹ️ Automatic student eligibility verification is not enabled."
    )


def main():
    token = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError(
            "Missing bot token. Set BOT_TOKEN (or TELEGRAM_BOT_TOKEN) on the Railway service."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    Thread(target=serve_health, daemon=True, name="http-health").start()
    logger.info("PPYXR Telegram bot starting")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
