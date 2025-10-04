import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Константы
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Простой словарь для хранения сообщений
user_messages = {}

# Клавиатура
user_keyboard = ReplyKeyboardMarkup([
    ["Написать ещё 😊", "Удалить сообщение 😊"]
], resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Привет! Отправь мне сообщение, и я перешлю его администратору.",
        reply_markup=user_keyboard
    )

def handle_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    
    # Сохраняем сообщение
    user_messages[user.id] = {
        'text': update.message.text or "Медиа-сообщение",
        'message_id': update.message.message_id
    }
    
    # Подтверждение пользователю
    update.message.reply_text(
        "✅ Сообщение отправлено, ожидайте ответ!",
        reply_markup=user_keyboard
    )
    
    # Пересылаем админу
    try:
        if update.message.text:
            context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📨 Сообщение от {user.first_name}:\n\n{update.message.text}"
            )
        else:
            update.message.forward(ADMIN_CHAT_ID)
    except Exception as e:
        print(f"Ошибка: {e}")

def delete_message(update: Update, context: CallbackContext):
    user = update.message.from_user
    if user.id in user_messages:
        try:
            context.bot.delete_message(
                chat_id=user.id,
                message_id=user_messages[user.id]['message_id']
            )
            update.message.reply_text("✅ Сообщение удалено!", reply_markup=user_keyboard)
        except Exception as e:
            update.message.reply_text("❌ Ошибка удаления", reply_markup=user_keyboard)
    else:
        update.message.reply_text("❌ Нечего удалять", reply_markup=user_keyboard)

def new_message(update: Update, context: CallbackContext):
    update.message.reply_text("✍️ Отправьте новое сообщение:", reply_markup=user_keyboard)

def main():
    if not TOKEN:
        print("❌ Токен не найден!")
        return
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex("Написать ещё 😊"), new_message))
    dispatcher.add_handler(MessageHandler(Filters.regex("Удалить сообщение 😊"), delete_message))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    print("🔄 Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()