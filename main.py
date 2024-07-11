from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers import welcome, start, text_handler, fort_boyard_callback, handle_shop, leaderboard, show_profile, exit_game, use_hint, contact_manager, reply_to_client, forward_message_to_client, MANAGER_CHAT_ID

TOKEN = '7082166356:AAG0SF3nnbO7f2YSm0yPV8lBlxhM2vWxjak'  # Замените на ваш реальный токен

def main():
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler('start', start))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.Chat(MANAGER_CHAT_ID), forward_message_to_client))
    
    # Обработчики колбэков для кнопок
    application.add_handler(CallbackQueryHandler(fort_boyard_callback, pattern="^challenge_"))
    application.add_handler(CallbackQueryHandler(handle_shop, pattern="^shop_"))
    application.add_handler(CallbackQueryHandler(exit_game, pattern="^exit_game$"))
    application.add_handler(CallbackQueryHandler(use_hint, pattern="^confirm_hint|cancel_hint$"))
    application.add_handler(CallbackQueryHandler(reply_to_client, pattern="^reply_"))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
