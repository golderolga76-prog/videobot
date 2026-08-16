import os

import modal
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
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
        [
            InlineKeyboardButton(
                "🎬 Создать видео",
                callback_data="create_video",
            )
        ],
        [
            InlineKeyboardButton(
                "🤖 AI Assistant",
                url="https://t.me/ASSISTENTAI_bot",
            )
        ],
        [
            InlineKeyboardButton(
                "🌐 VeoStudio",
                url="https://getveostudio.app",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["waiting_prompt"] = False

    await update.message.reply_text(
        "🎬 Добро пожаловать в VeoStudio AI Video!\n\n"
        "Создавайте AI-видео прямо в Telegram.\n\n"
        "Выберите действие:",
        reply_markup=main_menu(),
    )


async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.data == "create_video":
        context.user_data["waiting_prompt"] = True

        await query.message.reply_text(
            "🎬 Напишите, какое видео вы хотите создать.\n\n"
            "Например:\n"
            "Белая лошадь бежит по берегу моря на закате."
        )


async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.user_data.get("waiting_prompt"):
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu(),
        )
        return

    prompt = update.message.text.strip()
    context.user_data["waiting_prompt"] = False

    status_message = await update.message.reply_text(
        "⏳ Создаю ваше видео...\n\n"
        "Это может занять несколько минут."
    )

    try:
        generate_video = modal.Function.from_name(
            "veostudio-video",
            "generate_video",
        )

        video_bytes = await generate_video.remote.aio(prompt)

        video = InputFile(
            video_bytes,
            filename="veostudio.mp4",
        )

        await update.message.reply_video(
            video=video,
            caption=(
                "✅ Видео готово!\n\n"
                "🎬 VeoStudio AI Video"
            ),
            supports_streaming=True,
            write_timeout=120,
            read_timeout=120,
            connect_timeout=30,
        )

        await status_message.delete()

        await update.message.reply_text(
            "Создать ещё одно видео?",
            reply_markup=main_menu(),
        )

    except Exception as e:
        print("VIDEO GENERATION ERROR:", repr(e))

        await status_message.edit_text(
            "❌ Не удалось создать видео.\n\n"
            "Попробуйте ещё раз немного позже."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_click)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_message,
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
