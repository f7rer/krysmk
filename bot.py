import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from datetime import datetime

# Конфиг говна
TOKEN = "7714851697:AAEt--N1Ow26PWvyFNLn5Ezgw9y1dmS1IQ8"
CHANNEL = "@krysmk"
MAIN_ADMIN = 8011529449
ADMINS = [6874908262]
GREETING = "Йоу, петушара! Кидай сюда свою похабщину 🐷\nРазместим, если не сосём 💅"
FOOTER = "\n\n[Слить суку](https://t.me/fadewithinbot)"

# Состояния для редактуры
EDITING = 1

# Хранилище для постов
posts_data = {}
pending_edits = {}

# Настройка логов
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Связь", callback_data="contact")]]
    await update.message.reply_text(GREETING, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in ADMINS:
        return
    
    post = {
        "user_id": user.id,
        "username": f"@{user.username}" if user.username else "Без юзернейма",
        "user_name": user.first_name or "Аноним",
        "text": update.message.caption or "",
        "media": [],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "admin_msg_id": None  # Добавили для редактирования
    }

    if update.message.photo:
        post["media"].append(("photo", update.message.photo[-1].file_id))
    elif update.message.video:
        post["media"].append(("video", update.message.video.file_id))

    post_id = str(update.message.message_id)
    posts_data[post_id] = post

    for admin in ADMINS:
        try:
            await send_to_admin(context, post, admin, post_id)
        except Exception as e:
            logging.error(f"Админ {admin} сосёт: {e}")

async def send_to_admin(context, post, admin_id, post_id):
    buttons = [
        [
            InlineKeyboardButton("💩 Удалить", callback_data=f"delete_{post_id}"),
            InlineKeyboardButton("🚀 Отправить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{post_id}"),
        ]
    ]

    caption = f"{post['text']}"
    if admin_id == MAIN_ADMIN:
        user_link = f"[{post['user_name']}](tg://user?id={post['user_id']})"
        caption += f"\n\n👤 От: {user_link} ({post['username']})\n🕒 {post['date']}"

    try:
        if post["media"]:
            media_type, file_id = post["media"][0]
            if media_type == "photo":
                msg = await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode="Markdown"
                )
            else:
                msg = await context.bot.send_video(
                    chat_id=admin_id,
                    video=file_id,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode="Markdown"
                )
        else:
            msg = await context.bot.send_message(
                chat_id=admin_id,
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )
        # Сохраняем ID сообщения у админа
        posts_data[post_id]['admin_msg_id'] = msg.message_id
    except Exception as e:
        logging.error(f"Не удалось послать админу: {e}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "contact":
        response = (
            "🖕Связь с админами? Да ты шаришь за мемы! Пишешь сюда — мы постим. Хочешь диалог? "
            "Пидарасу из Роскомнадзора звони, тут только анонимный движ.\n\n"
            "🔥 Предлагаешь заняться моей личной жизнью? Спасибо, папаша, сам разберусь с твоей женой. "
            "Угрозы? Да мы их ссаными тряпками вытираем — смешно, блять, слышать сопли малолетки.\n\n"
            "🧑⚖️ По закону все чисто: 18+ не постим, на полицию нам насрать — они сами знают, "
            "что ты дауничок, если придешь с такими заявлениями.\n\n"
            "💩 Выбор за тобой: хочешь — гадь, хочешь — хвали. Только помни: "
            "в прошлый раз вы все орали как всё плохо, а как надо было хорошее постить — "
            "пришлось вам жопу пинком раскрывать. Теперь думай своей башкой, мудила."
        )
        await query.edit_message_text(response, parse_mode="Markdown")
        return

    action, post_id = query.data.split('_')
    post = posts_data.get(post_id)

    if not post:
        await query.answer("Пост уже в жопе!")
        return

    if action == "delete":
        del posts_data[post_id]
        await query.message.delete()
        await query.answer("Пост удалён нахуй!")
    
    elif action == "approve":
        await send_to_channel(context, post)
        del posts_data[post_id]
        await query.message.delete()
        await query.answer("Залил в канал, доволен?")
    
    elif action == "edit":
        pending_edits[query.from_user.id] = post_id
        await query.message.reply_text("Шли новый текст, пидрила:")
        return EDITING

async def send_to_channel(context, post):
    caption = f"{post['text']}{FOOTER}"
    try:
        if post["media"]:
            media_type, file_id = post["media"][0]
            if media_type == "photo":
                await context.bot.send_photo(
                    chat_id=CHANNEL,
                    photo=file_id,
                    caption=caption,
                    parse_mode="Markdown"
                )
            else:
                await context.bot.send_video(
                    chat_id=CHANNEL,
                    video=file_id,
                    caption=caption,
                    parse_mode="Markdown"
                )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL,
                text=caption,
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Не прокатило в канал: {e}")

async def edit_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in pending_edits:
        return
    
    post_id = pending_edits[user_id]
    post = posts_data.get(post_id)
    post['text'] = update.message.text
    del pending_edits[user_id]
    
    for admin in ADMINS:
        try:
            await update_admin_post(context, post, admin, post_id)
        except Exception as e:
            logging.error(f"Админ {admin} обосрался: {e}")
    
    await update.message.reply_text("Исправлено, ебать!")
    return ConversationHandler.END

async def update_admin_post(context, post, admin_id, post_id):
    buttons = [
        [
            InlineKeyboardButton("💩 Удалить", callback_data=f"delete_{post_id}"),
            InlineKeyboardButton("🚀 Отправить", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{post_id}"),
        ]
    ]

    caption = f"{post['text']}"
    if admin_id == MAIN_ADMIN:
        user_link = f"[{post['user_name']}](tg://user?id={post['user_id']})"
        caption += f"\n\n👤 От: {user_link} ({post['username']})\n🕒 {post['date']}"

    try:
        if post["media"]:
            media_type, file_id = post["media"][0]
            if media_type == "photo":
                await context.bot.edit_message_caption(
                    chat_id=admin_id,
                    message_id=post['admin_msg_id'],
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode="Markdown"
                )
            else:
                await context.bot.edit_message_caption(
                    chat_id=admin_id,
                    message_id=post['admin_msg_id'],
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode="Markdown"
                )
        else:
            await context.bot.edit_message_text(
                chat_id=admin_id,
                message_id=post['admin_msg_id'],
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Не смог обновить: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click)],
        states={
            EDITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_post)]
        },
        fallbacks=[],
        per_message=True  # Фикс для ебучих состояний
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT, handle_media))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        poll_interval=2,  # На всякий пожарный
        timeout=30
    )

if __name__ == "__main__":
    main()
