import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")


def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎬 Создать видео", callback_data="create_video")],
        [InlineKeyboardButton("🤖 AI Assistant", url="https://t.me/ASSISTENTAI_bot")],
        [InlineKeyboardButton("🌐 VeoStudio", url="https://getveostudio.app")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["waiting_prompt"] = False

    await update.message.reply_text(
        "🎬 Добро пожаловать в VeoStudio AI Video!\n\n"
        "Создавайте AI-видео прямо в Telegram.\n\n"
        "Выберите действие:",
        reply_markup=main_menu(),
    )


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_video":
        context.user_data["waiting_prompt"] = True

        await query.message.reply_text(
            "🎬 Напишите, какое видео вы хотите создать.\n\n"
            "Например:\n"
            "Белая лошадь бежит по берегу моря на закате."
        )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_prompt"):
        prompt = update.message.text
        context.user_data["waiting_prompt"] = False

        await update.message.reply_text(
            "✅ Описание принято!\n\n"
            f"🎬 {prompt}\n\n"
            "Генерацию видео подключим следующим шагом."
        )
    else:
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu(),
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    app.run_polling()


if name == "main":
    main()
