import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Константы
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения сообщений
user_messages = {}

# Клавиатура
def get_user_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Написать ещё 😊"))
    keyboard.add(KeyboardButton("Удалить сообщение 😊"))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! Отправь мне сообщение, и я перешлю его администратору.",
        reply_markup=get_user_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == "Написать ещё 😊")
def new_message(message):
    bot.send_message(message.chat.id, "✍️ Отправьте ваше новое сообщение:", reply_markup=get_user_keyboard())

@bot.message_handler(func=lambda message: message.text == "Удалить сообщение 😊")
def delete_message(message):
    user_id = message.from_user.id
    if user_id in user_messages:
        try:
            bot.delete_message(user_id, user_messages[user_id]['message_id'])
            del user_messages[user_id]
            bot.send_message(message.chat.id, "✅ Сообщение удалено!", reply_markup=get_user_keyboard())
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Не удалось удалить сообщение", reply_markup=get_user_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Не найдено сообщений для удаления", reply_markup=get_user_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user = message.from_user
    
    # Сохраняем сообщение
    user_messages[user.id] = {
        'text': message.text or "Медиа-сообщение", 
        'message_id': message.message_id
    }
    
    # Подтверждение пользователю
    bot.send_message(
        message.chat.id,
        "✅ Сообщение отправлено, ожидайте ответ!",
        reply_markup=get_user_keyboard()
    )
    
    # Пересылаем админу
    try:
        if message.text:
            bot.send_message(
                ADMIN_CHAT_ID,
                f"📨 Сообщение от {user.first_name} (@{user.username}):\n\n{message.text}"
            )
        else:
            bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
            bot.send_message(
                ADMIN_CHAT_ID,
                f"📨 Медиа-сообщение от {user.first_name} (@{user.username})"
            )
    except Exception as e:
        print(f"Ошибка пересылки: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка отправки сообщения", reply_markup=get_user_keyboard())

if __name__ == "__main__":
    print("🔄 Бот запускается...")
    bot.infinity_polling()