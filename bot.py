import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    ConversationHandler
)
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Состояния для ConversationHandler
WAITING_FOR_REPLY = 1

# Глобальные переменные для хранения данных
user_messages = {}

# Клавиатура для пользователя
user_keyboard = ReplyKeyboardMarkup([
    ["Написать ещё 😊", "Удалить сообщение 😊"]
], resize_keyboard=True)

# Клавиатура для админа
admin_keyboard = ReplyKeyboardMarkup([
    ["Ответить пользователю"]
], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот-пересыльщик сообщений. "
        "Отправь мне любое сообщение, и я перешлю его администратору.\n\n"
        "После отправки ты увидишь подтверждение и сможешь:\n"
        "• Отправить новое сообщение\n"
        "• Удалить отправленное сообщение",
        reply_markup=user_keyboard
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений от пользователя и пересылка админу"""
    user = update.message.from_user
    message = update.message
    
    # Сохраняем информацию о сообщении
    user_messages[user.id] = {
        'text': message.text or "Медиа-сообщение",
        'message_id': message.message_id,
        'username': user.username or user.first_name
    }
    
    # Отправляем подтверждение пользователю
    await update.message.reply_text(
        "✅ Сообщение отправлено, ожидайте ответ!\n\n"
        "Вы можете:\n"
        "• Написать новое сообщение\n"
        "• Удалить это сообщение",
        reply_markup=user_keyboard
    )
    
    # Пересылаем сообщение админу
    try:
        if message.text:
            # Текстовое сообщение
            forwarded_msg = await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📨 Новое сообщение от @{user.username or user.first_name}:\n\n{message.text}",
                reply_markup=admin_keyboard
            )
        else:
            # Медиа-сообщение
            forwarded_msg = await message.forward(ADMIN_CHAT_ID)
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📨 Медиа-сообщение от @{user.username or user.first_name}",
                reply_markup=admin_keyboard
            )
        
        user_messages[user.id]['forwarded_id'] = forwarded_msg.message_id
        
    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")
        await update.message.reply_text("❌ Ошибка отправки сообщения")

async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление сообщения пользователя"""
    user = update.message.from_user
    
    if user.id in user_messages:
        try:
            # Удаляем у админа
            if 'forwarded_id' in user_messages[user.id]:
                await context.bot.delete_message(
                    chat_id=ADMIN_CHAT_ID,
                    message_id=user_messages[user.id]['forwarded_id']
                )
            
            # Удаляем оригинал
            await context.bot.delete_message(
                chat_id=user.id,
                message_id=user_messages[user.id]['message_id']
            )
            
            del user_messages[user.id]
            await update.message.reply_text("✅ Сообщение удалено!", reply_markup=user_keyboard)
            
        except Exception as e:
            logger.error(f"Ошибка удаления: {e}")
            await update.message.reply_text("❌ Не удалось удалить сообщение", reply_markup=user_keyboard)
    else:
        await update.message.reply_text("❌ Не найдено сообщений для удаления", reply_markup=user_keyboard)

async def new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Написать ещё'"""
    await update.message.reply_text("✍️ Отправьте ваше новое сообщение:", reply_markup=user_keyboard)

async def start_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ответа админа пользователю"""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        return
    
    await update.message.reply_text(
        "Введите ID пользователя и сообщение для ответа в формате:\n"
        "`123456789 Ваш текст ответа`\n\n"
        "ID пользователя можно узнать из пересланных сообщений.",
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_REPLY

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответа админа"""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        return
    
    try:
        text = update.message.text
        user_id, reply_text = text.split(' ', 1)
        user_id = int(user_id)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Ответ от администратора:\n\n{reply_text}",
            reply_markup=user_keyboard
        )
        
        await update.message.reply_text("✅ Ответ отправлен пользователю!", reply_markup=admin_keyboard)
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: `ID_пользователя Текст ответа`",
            parse_mode='Markdown',
            reply_markup=admin_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка отправки ответа: {e}")
        await update.message.reply_text("❌ Ошибка отправки ответа", reply_markup=admin_keyboard)
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text("Диалог отменен")
    return ConversationHandler.END

def main():
    """Основная функция"""
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики кнопок
    application.add_handler(MessageHandler(filters.Regex("Написать ещё 😊"), new_message))
    application.add_handler(MessageHandler(filters.Regex("Удалить сообщение 😊"), delete_message))
    
    # Обработчик ответов админа
    reply_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Ответить пользователю"), start_admin_reply)],
        states={
            WAITING_FOR_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(reply_conversation)
    
    # Обработчик обычных сообщений
    application.add_handler(MessageHandler(filters.ALL, handle_user_message))
    
    # Запуск бота
    print("🔄 Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()