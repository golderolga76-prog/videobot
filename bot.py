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


def main_menu(user_id=None):
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

    if str(user_id) == str(ADMIN_ID):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "👱 Мой AI-двойник",
                    callback_data="my_avatar",
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    users = load_users()
    record = get_user_record(users, update.effective_user.id)

    if not record.get("started_at"):
        record["started_at"] = datetime.now(timezone.utc).isoformat()

    record["username"] = update.effective_user.username or ""
    record["first_name"] = update.effective_user.first_name or ""

    save_users(users)

    context.user_data["waiting_prompt"] = False

    await update.message.reply_text(
        "🎬 Добро пожаловать в VeoStudio AI Video!\n\n"
        "Создавайте AI-видео прямо в Telegram.\n\n"
        "Выберите действие:",
   reply_markup=main_menu(update.effective_user.id),
    )    


async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    print("CALLBACK:", query.data, "USER:", query.from_user.id)

    # Мой AI-двойник
    if query.data == "my_avatar":
        if str(query.from_user.id) != str(ADMIN_ID):
            await query.edit_message_text("Эта функция недоступна.")
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "🏢 Офис",
                    callback_data="avatar:office",
                ),
                InlineKeyboardButton(
                    "🤖 AI-студия",
                    callback_data="avatar:studio_beige",
                ),
            ],
            [
                InlineKeyboardButton(
                    "☕ Кафе",
                    callback_data="avatar:cafe_beige",
                ),
                InlineKeyboardButton(
                    "🩵 Голубой пиджак",
                    callback_data="avatar:blue",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🎥 Видео-двойник",
                    callback_data="video_twin",
                ),
            ],
        ]

        await query.edit_message_text(
            "👩 Выберите образ для AI-двойника:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
        if query.data == "video_twin":
        keyboard = [
            [
                InlineKeyboardButton("🏢 Офис", callback_data="twin:office"),
                InlineKeyboardButton("🤖 AI-студия", callback_data="twin:studio_beige"),
            ],
            [
                InlineKeyboardButton("☕ Кафе", callback_data="twin:cafe_beige"),
                InlineKeyboardButton("🩵 Голубой пиджак", callback_data="twin:blue"),
            ],
        ]

        await query.edit_message_text(
            "🎥 Выберите образ для Видео-двойника:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    # Выбор образа AI-двойника
    if query.data.startswith("twin:"):
        if str(query.from_user.id) != str(ADMIN_ID):
            await query.edit_message_text("Эта функция недоступна.")
            return

    avatar_name = query.data.split(":", 1)[1]

    context.user_data["twin_avatar"] = avatar_name
    context.user_data["waiting_twin_video"] = True

    await query.edit_message_text(
        "🎥 Образ выбран.\n\n"
        "Теперь отправьте короткое видео 4–6 секунд.\n"
        "Смотрите в камеру, двигайтесь спокойно и без резких поворотов головы."
    )
    return
    if query.data.startswith("avatar:"):
        if str(query.from_user.id) != str(ADMIN_ID):
            await query.edit_message_text("Эта функция недоступна.")
            return

        avatar_name = query.data.split(":", 1)[1]

        context.user_data["avatar_image"] = avatar_name
        context.user_data["waiting_avatar_text"] = True
        context.user_data["waiting_prompt"] = False

        await query.edit_message_text(
            "✍️ Теперь напишите текст, который должен произнести ваш AI-двойник."
        )
        return

    # Обычное создание видео
    if query.data == "create_video":
        users = load_users()
        record = get_user_record(users, query.from_user.id)

        if record["free_month"] != current_month():
            context.user_data["video_access"] = "free"

        elif record["gifts"] > 0:
            context.user_data["video_access"] = "gift"

        else:
            buy_keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🎁 Купить пакет и получить видео в подарок",
                            url="https://getveostudio.app",
                        )
                    ]
                ]
            )

            await query.message.reply_text(
                "Вы уже использовали бесплатное видео в этом месяце.\n\n"
                "🎁 Купите первый пакет VeoStudio за 249 грн — "
                "и получите ещё одно 5-секундное видео в подарок.",
                reply_markup=buy_keyboard,
            )
            return

        context.user_data["waiting_prompt"] = True
        context.user_data["waiting_avatar_text"] = False

        await query.message.reply_text(
            "🎬 Напишите, какое видео вы хотите создать.\n\n"
            "Например:\n"
            "Белая лошадь бежит по берегу моря на закате."
        )
        return
async def text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
  ):
    if (
        not context.user_data.get("waiting_prompt")
        and not context.user_data.get("waiting_avatar_text")
    ):
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=main_menu(update.effective_user.id),
        )
        return
      
    prompt = update.message.text.strip()

    if context.user_data.get("waiting_avatar_text"):
        context.user_data["waiting_avatar_text"] = False

        avatar_name = context.user_data.get("avatar_image", "office")

        status_message = await update.message.reply_text(
            "🎭 Создаю видео вашего AI-двойника...\n\n"
            "Сначала создаю голос, затем видео. Это может занять несколько минут."
        )

        try:    
            generate_voice = modal.Function.from_name(
                "veostudio-voice",
                "generate_voice",
            )

            audio_bytes = await generate_voice.remote.aio(prompt)

            generate_avatar = modal.Function.from_name(
                "veostudio-avatar-api",
                "generate_avatar_bot",
            )

            video_bytes = await generate_avatar.remote.aio(
                avatar_name,
                audio_bytes,
            )

            video = InputFile(
                video_bytes,
                filename="my_ai_avatar.mp4",
            )

            await update.message.reply_video(
                video=video,
                caption="✅ Видео вашего AI-двойника готово!",
                supports_streaming=True,
                write_timeout=120,
                read_timeout=120,
                connect_timeout=30,
            )

            context.user_data.pop("avatar_image", None)

            await status_message.delete()

            await update.message.reply_text(
                "Создать ещё одно видео?",
                reply_markup=main_menu(update.effective_user.id),
            )
            return

        except Exception as e:
            print("AVATAR VIDEO ERROR:", repr(e))

            await status_message.edit_text(
                "❌ Не удалось создать видео AI-двойника.\n"
                "Попробуйте ещё раз."
            )
            return
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
        record = get_user_record(
            users,
            update.effective_user.id,
        )

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
async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
   ):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ Нет доступа.")
        return

    users = load_users()

    total_users = len(users)
    started_users = sum(
        1 for record in users.values()
        if record.get("started_at")
    )
    free_this_month = sum(
        1 for record in users.values()
        if record.get("free_month") == current_month()
    )
    gifts_available = sum(
        int(record.get("gifts", 0) or 0)
        for record in users.values()
    )

    await update.message.reply_text(
        "📊 Статистика VeoStudio AI Video\n\n"
        f"👥 Всего пользователей в базе: {total_users}\n"
        f"▶️ Нажали Start: {started_users}\n"
        f"🎁 Использовали бесплатное видео в этом месяце: {free_this_month}\n"
        f"🎬 Подарочных видео на балансах: {gifts_available}"
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
async def voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.user_data.get("waiting_avatar_text"):
        await update.message.reply_text(
            "Сначала выберите «Мой AI-двойник» и нужный образ."
        )
        return

    avatar_name = context.user_data.get("avatar_image", "office")

    status_message = await update.message.reply_text(
        "🎙 Получила ваш голос.\n"
        "🎬 Создаю видео AI-двойника..."
    )

    try:
        voice = update.message.voice
        tg_file = await context.bot.get_file(voice.file_id)

        audio_bytes = await tg_file.download_as_bytearray()

        generate_avatar = modal.Function.from_name(
            "veostudio-avatar-api",
            "generate_avatar_bot",
        )

        video_bytes = await generate_avatar.remote.aio(
            avatar_name,
            bytes(audio_bytes),
        )

        video = InputFile(
            video_bytes,
            filename="my_ai_avatar_voice.mp4",
        )

        await update.message.reply_video(
            video=video,
            caption="✅ Видео вашего AI-двойника готово!",
            supports_streaming=True,
            write_timeout=120,
            read_timeout=120,
            connect_timeout=30,
        )

        context.user_data.pop("avatar_image", None)
        context.user_data["waiting_avatar_text"] = False

        await status_message.delete()

        await update.message.reply_text(
            "Создать ещё одно видео?",
            reply_markup=main_menu(update.effective_user.id),
        )

    except Exception as e:
        print("AVATAR VOICE ERROR:", repr(e))

        await status_message.edit_text(
            "❌ Не удалось создать видео из голосового сообщения.\n"
            "Попробуйте ещё раз."
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
        CommandHandler("stats", stats)
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
    app.add_handler(
        MessageHandler(filters.VOICE, voice_message
                      )
    )

    app.run_polling()

if __name__ == "__main__":
    main()
