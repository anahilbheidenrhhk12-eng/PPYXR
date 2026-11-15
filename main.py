"""Railway entrypoint: PPYXR Telegram support and official eligibility navigation.

Original modules are left unchanged and not imported here.
"""
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("PPYXR")


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 Official student verification", url="https://one.google.com/ai-student")],
        [InlineKeyboardButton("📩 Support", url="https://t.me/DigHelptbot")],
        [InlineKeyboardButton("👥 Support group", url="https://t.me/digitrust22")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "👋 Welcome to PPYXR!\n\n"
        "🎓 Open the official student verification service with the button below.\n"
        "📩 For assistance use the support buttons.",
        reply_markup=menu(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ Open the official eligibility page and follow its instructions.\n"
        "The automated verification module is not available in this deployment.",
        reply_markup=menu(),
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("✅ PPYXR Telegram bot is running.")


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_error(404)
            return
        body = b"ok\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        log.debug(fmt, *args)


async def on_ready(app: Application):
    me = await app.bot.get_me()
    log.info("Telegram connected as @%s", me.username)


def main():
    token = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("Missing BOT_TOKEN or TELEGRAM_BOT_TOKEN in Railway variables.")
    app = Application.builder().token(token).post_init(on_ready).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("verify", help_command))
    app.add_handler(CommandHandler("status", status))
    port = int(os.getenv("PORT", "8080"))
    Thread(target=lambda: ThreadingHTTPServer(("0.0.0.0", port), Health).serve_forever(), daemon=True).start()
    log.info("Starting Telegram polling")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
