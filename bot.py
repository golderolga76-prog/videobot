import os
import json
from datetime import datetime, timezone

for key in ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"):
    value = os.getenv(key)
    if value:
        os.environ[key] = (
            value
            .replace("\n", "")
            .replace("\r", "")
            .replace("\\n", "")
            .strip()
        )

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
ADMIN_ID = os.getenv("ADMIN_ID")
DATA_FILE = "/data/video_users.json"

def load_users():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
def current_month():
    return datetime.now(timezone.utc).strftime("%Y-%m")

def get_user_record(users, user_id):
    key = str(user_id)
    if key not in users:
        users[key] = {
            "free_month": "",
            "gifts": 0
        }
    return users[key]


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
            url="https://t.me/AIasistent_bot",
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
    users = load_users()
    record = get_user_record(users, query.from_user.id)

    if record["free_month"] != current_month():
        context.user_data["video_access"] = "free"
    elif record["gifts"] > 0:
        context.user_data["video_access"] = "gift"
    else:
        buy_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🎁 Купить пакет и получить видео в подарок",
                    url="https://getveostudio.app"
                )
            ]
        ])

        await query.message.reply_text(
            "Вы уже использовали бесплатное видео в этом месяце.\n\n"
            "🎁 Купите первый пакет VeoStudio за 249 грн — "
            "и получите ещё одно 5-секундное видео в подарок.",
            reply_markup=buy_keyboard,
        )
        return

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
      users = load_users()
      record = get_user_record(users, update.effective_user.id)

      access_type = context.user_data.get("video_access")

      if access_type == "free":
        record["free_month"] = current_month()
      elif access_type == "gift" and record["gifts"] > 0:
        record["gifts"] -= 1

      save_users(users)
        context.user_data.pop("video_access", None)
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
async def gift_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /gift TELEGRAM_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный Telegram ID.")
        return

    users = load_users()
    record = get_user_record(users, user_id)
    record["gifts"] += 1
    save_users(users)

    await update.message.reply_text(
        f"✅ Пользователю {user_id} начислено 1 подарочное видео."
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )
    app.add_handler(
    CommandHandler("gift", gift_video)
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
