"""PPYXR Telegram entrypoint. Original project modules remain unchanged.

This entrypoint provides the available Telegram interface and link-format check.
The original automatic verification workflow is not complete in this repository.
"""
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

from telegram import (
    BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands, Update,
    BotCommandScopeDefault, BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats, BotCommandScopeAllChatAdministrators,
    BotCommandScopeChat,
)
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("PPYXR")

OFFICIAL_URL = "https://one.google.com/ai-student"
COMMANDS = [
    BotCommand("start", "Open main menu"),
    BotCommand("verify", "Student verification instructions"),
    BotCommand("help", "Help and support"),
    BotCommand("status", "Bot status"),
]


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 Verify Student", callback_data="verify")],
        [InlineKeyboardButton("📖 Help & Guide", callback_data="help")],
        [InlineKeyboardButton("📩 Support", url="https://t.me/DigHelptbot"),
         InlineKeyboardButton("👥 Support Group", url="https://t.me/digitrust22")],
    ])


def verify_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Open Official Student Offer", url=OFFICIAL_URL)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
    ])


def guide_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 Verify Student", callback_data="verify"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="home")],
        [InlineKeyboardButton("📩 Support", url="https://t.me/DigHelptbot")],
    ])


async def refresh_chat_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Override old per-chat and language-scoped menus from the previous bot."""
    chat = update.effective_chat
    if not chat or chat.type != "private":
        return
    language = (update.effective_user.language_code or "").lower().split("-")[0]
    for lang in (None, language or None):
        try:
            await context.bot.set_my_commands(
                COMMANDS, scope=BotCommandScopeChat(chat_id=chat.id), language_code=lang
            )
        except Exception as exc:
            log.warning("Could not refresh commands in chat %s (%s)", chat.id, type(exc).__name__)
    try:
        await context.bot.set_chat_menu_button(chat_id=chat.id, menu_button=MenuButtonCommands())
    except Exception as exc:
        log.warning("Could not refresh menu button (%s)", type(exc).__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("expect_link", None)
    await refresh_chat_commands(update, context)
    await update.effective_message.reply_text(
        "👋 WELCOME TO PPYXR! 🎓\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎓 Student Verification\n"
        "📖 Help & Guide\n"
        "📩 Support & Community\n\n"
        "Choose an option below:",
        reply_markup=menu(),
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expect_link"] = True
    text = (
        "🎓 GOOGLE STUDENT VERIFICATION\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. Open the official student offer page.\n"
        "2. Choose the student plan and follow the official verification steps.\n"
        "3. If you already have a verification URL, send 1–3 full links,\n"
        "   one per line, to check their format:\n"
        "https://services.sheerid.com/verify/...\n\n"
        "ℹ️ A link-format check does not verify student eligibility. "
        "The original automatic verification processor is not available in this deployment."
    )
    await update.effective_message.reply_text(
        text, reply_markup=verify_menu(), disable_web_page_preview=True
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "💬 HELP CENTER & USER GUIDE\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎓 Verify Student — open the official student offer and follow its steps.\n"
        "🔗 Send a services.sheerid.com/verify/ link to check its format.\n"
        "📩 Support: @DigHelptbot\n"
        "👥 Group: https://t.me/digitrust22\n\n"
        "The original automatic verification processor is not configured here.",
        reply_markup=guide_menu(), disable_web_page_preview=True,
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "✅ PPYXR Telegram bot is online.\n"
        "ℹ️ Automatic verification is not active.",
        reply_markup=menu(),
    )


def is_verification_url(value):
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https"
                and parsed.hostname == "services.sheerid.com"
                and parsed.path.startswith("/verify/")
                and len(parsed.path) > len("/verify/")
                and len(value) < 2000)
    except ValueError:
        return False


async def text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (update.effective_message.text or "").strip()
    links = [value.strip() for value in msg.splitlines() if value.strip()]
    if not context.user_data.get("expect_link"):
        if links and all(is_verification_url(link) for link in links):
            context.user_data["expect_link"] = True
        else:
            await update.effective_message.reply_text(
                "Use /start to open the main menu.", reply_markup=menu()
            )
            return
    if not (1 <= len(links) <= 3) or not all(is_verification_url(link) for link in links):
        await update.effective_message.reply_text(
            "⚠️ Invalid link format. Send 1–3 full https://services.sheerid.com/verify/... URLs, one per line.",
            reply_markup=verify_menu(), disable_web_page_preview=True,
        )
        return
    context.user_data.pop("expect_link", None)
    await update.effective_message.reply_text(
        f"✅ {len(links)} verification link(s) have a valid URL format.\n\n"
        "This is only a format check. Your eligibility is not confirmed, "
        "and this bot does not automatically submit verification requests. "
        "Continue verification on the official website.",
        reply_markup=verify_menu(), disable_web_page_preview=True,
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    action = q.data
    if action == "verify":
        await verify(update, context)
    elif action == "help":
        await help_command(update, context)
    elif action in ("home", "cancel"):
        context.user_data.pop("expect_link", None)
        await q.message.reply_text("🏠 PPYXR MAIN MENU", reply_markup=menu())


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
    # Telegram retains old bot commands until explicitly overwritten. Refresh
    # each global scope and supported private-language scope from the old project.
    scopes = (
        BotCommandScopeDefault(),
        BotCommandScopeAllPrivateChats(),
        BotCommandScopeAllGroupChats(),
        BotCommandScopeAllChatAdministrators(),
    )
    for scope in scopes:
        try:
            await app.bot.set_my_commands(COMMANDS, scope=scope)
        except Exception as exc:
            log.warning("Could not replace %s commands (%s)", type(scope).__name__, type(exc).__name__)
    for language in ("en", "ar", "fr", "es", "pt", "ru", "tr", "vi", "id"):
        try:
            await app.bot.set_my_commands(
                COMMANDS, scope=BotCommandScopeAllPrivateChats(), language_code=language
            )
        except Exception as exc:
            log.warning("Could not update %s commands (%s)", language, type(exc).__name__)
    try:
        await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception as exc:
        log.warning("Could not set menu button (%s)", type(exc).__name__)
    me = await app.bot.get_me()
    log.info("Telegram connected as @%s; command menu refreshed", me.username)


def main():
    token = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("Missing BOT_TOKEN or TELEGRAM_BOT_TOKEN in Railway variables.")
    app = Application.builder().token(token).post_init(on_ready).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify", verify))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(callback, pattern="^(verify|help|home|cancel)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input))
    port = int(os.getenv("PORT", "8080"))
    Thread(
        target=lambda: ThreadingHTTPServer(("0.0.0.0", port), Health).serve_forever(),
        daemon=True,
        name="health-http",
    ).start()
    log.info("Starting Telegram polling")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
