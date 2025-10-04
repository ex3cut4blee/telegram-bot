import os
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, Text
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Словарь для хранения сообщений
user_messages = {}

# Клавиатура
user_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Написать ещё 😊"), KeyboardButton(text="Удалить сообщение 😊")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне сообщение, и я перешлю его администратору.",
        reply_markup=user_keyboard
    )

@dp.message(Text("Написать ещё 😊"))
async def new_message(message: types.Message):
    await message.answer("✍️ Отправьте ваше новое сообщение:", reply_markup=user_keyboard)

@dp.message(Text("Удалить сообщение 😊"))
async def delete_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_messages:
        try:
            await bot.delete_message(chat_id=user_id, message_id=user_messages[user_id]['message_id'])
            del user_messages[user_id]
            await message.answer("✅ Сообщение удалено!", reply_markup=user_keyboard)
        except Exception as e:
            await message.answer("❌ Не удалось удалить сообщение", reply_markup=user_keyboard)
    else:
        await message.answer("❌ Не найдено сообщений для удаления", reply_markup=user_keyboard)

@dp.message()
async def handle_all_messages(message: types.Message):
    user = message.from_user
    
    # Сохраняем сообщение
    user_messages[user.id] = {
        'text': message.text or "Медиа-сообщение",
        'message_id': message.message_id
    }
    
    # Подтверждение пользователю
    await message.answer(
        "✅ Сообщение отправлено, ожидайте ответ!",
        reply_markup=user_keyboard
    )
    
    # Пересылаем админу
    try:
        if message.text:
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📨 Сообщение от {user.first_name} (@{user.username}):\n\n{message.text}"
            )
        else:
            await message.forward(ADMIN_CHAT_ID)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📨 Медиа-сообщение от {user.first_name} (@{user.username})"
            )
    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")
        await message.answer("❌ Ошибка отправки сообщения", reply_markup=user_keyboard)

async def main():
    logger.info("🔄 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())