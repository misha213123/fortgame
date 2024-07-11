from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from game import get_random_challenge, pass_challenge, load_fort_boyard_data, save_fort_boyard_data, get_hint_for_challenge
from database import save_user_data, load_user_profile, update_user_profile, save_message_to_sequence, load_pending_messages, delete_message_from_sequence
import os
import sqlite3
import random
import string
from datetime import datetime, timedelta

MANAGER_CHAT_ID = 551270027  # Новый ID менеджера
manager_stats = {"replies": 0, "start_time": datetime.now()}  # Статистика работы менеджера
manager_info = {"first_name": "", "last_name": ""}  # Информация о менеджере

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE, new_registration=False):
    user_id = update.message.from_user.id
    stage, coins = load_fort_boyard_data(user_id)
    profile_data = load_user_profile(user_id)

    if user_id == MANAGER_CHAT_ID:
        if not manager_info["first_name"] or not manager_info["last_name"]:
            await update.message.reply_text('Пожалуйста, зарегистрируйтесь, введя свое имя:')
            context.user_data['step'] = 'manager_first_name'
        else:
            keyboard = [
                ["📋 Просмотр ожидающих сообщений", "🔍 Просмотр профиля клиента"],
                ["📊 Моя статистика"],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
            await update.message.reply_text("Добро пожаловать в панель менеджера.", reply_markup=reply_markup)
    elif profile_data:
        keyboard = [
            ["👤 Мой профиль", "🛒 Магазин"],
            ["ℹ️ О нас", "🏰 Пройти испытание"],
            ["🏆 Рейтинг игроков", "💡 Использовать подсказку"],
            ["📞 Связаться с менеджером"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        await update.message.reply_text("Добро пожаловать!", reply_markup=reply_markup)
    else:
        keyboard = [
            ["🚀 Начать", "ℹ️ О нас"],
            ["📞 Связаться с менеджером"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        await update.message.reply_text("Добро пожаловать! Для начала нажмите 'Начать'.", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await welcome(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id == MANAGER_CHAT_ID:
        if 'step' in context.user_data:
            step = context.user_data['step']
            if step == 'manager_first_name':
                manager_info["first_name"] = text
                context.user_data['step'] = 'manager_last_name'
                await update.message.reply_text('Введите вашу фамилию:')
            elif step == 'manager_last_name':
                manager_info["last_name"] = text
                del context.user_data['step']
                await update.message.reply_text('Регистрация завершена. Теперь вы можете работать с клиентами.')
                keyboard = [
                    ["📋 Просмотр ожидающих сообщений", "🔍 Просмотр профиля клиента"],
                    ["📊 Моя статистика"],
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
                await update.message.reply_text("Добро пожаловать в панель менеджера.", reply_markup=reply_markup)
        else:
            await handle_manager_commands(update, context, text)
        return

    if text == "🚀 Начать":
        await update.message.reply_text('Введите ваше имя:')
        context.user_data['step'] = 'first_name'
    elif text == "ℹ️ О нас":
        await update.message.reply_text(
            "Мы команда, готовая к новым вызовам и приключениям! 🌟\n\n"
            "Следите за нами в социальных сетях:\n"
            "Instagram: ссылка\n"
            "VK: ссылка\n"
            "Telegram: ссылка\n\n"
            "Наши контакты:\n"
            "Номер телефона: номер\n"
            "Второй номер: номер\n"
            "Email: почта\n"
            "Сайт: сайт\n"
        )
    elif text == "🏰 Пройти испытание":
        db_path = os.path.join(os.path.dirname(__file__), 'users.db')
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        conn.close()

        if data:
            keyboard = [
                ["👤 Мой профиль", "🛒 Магазин"],
                ["ℹ️ О нас", "🏰 Пройти испытание"],
                ["🏆 Рейтинг игроков", "💡 Использовать подсказку"],
                ["📞 Связаться с менеджером"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
            await update.message.reply_text("Испытание началось!", reply_markup=reply_markup)
            await fort_boyard(update, context)
        else:
            await update.message.reply_text("Для начала игры вам необходимо зарегистрироваться. Нажмите 'Начать'.")
    elif text == "🏆 Рейтинг игроков":
        await leaderboard(update, context)
    elif text == "💡 Использовать подсказку":
        stage, coins = load_fort_boyard_data(user_id)
        if stage == 0:
            await update.message.reply_text("Вы вышли из игры. Нажмите '🏰 Пройти испытание', чтобы продолжить.")
        elif coins >= 5:
            keyboard = [
                [InlineKeyboardButton("Да", callback_data="confirm_hint")],
                [InlineKeyboardButton("Нет", callback_data="cancel_hint")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Использование подсказки стоит 5 монет. Вы уверены, что хотите использовать подсказку?", reply_markup=reply_markup)
        else:
            await update.message.reply_text("У вас недостаточно монет для использования подсказки. Подсказка стоит 5 монет.")
    elif text == "🛒 Магазин":
        await show_shop(update, context)
    elif text == "👤 Мой профиль":
        await show_profile(update, context)
    elif text == "📞 Связаться с менеджером":
        context.user_data['awaiting_message'] = True
        await update.message.reply_text("Свободный менеджер скоро с вами свяжется. Напишите ваше сообщение:")
    elif text == "Выйти из игры":
        await exit_game(update, context)
    elif 'step' in context.user_data:
        step = context.user_data['step']

        if step == 'first_name':
            context.user_data['first_name'] = text
            context.user_data['step'] = 'last_name'
            await update.message.reply_text('Введите вашу фамилию:')
        elif step == 'last_name':
            context.user_data['last_name'] = text
            context.user_data['step'] = 'phone_number'
            await update.message.reply_text('Введите ваш номер телефона:')
        elif step == 'phone_number':
            context.user_data['phone_number'] = text
            context.user_data['step'] = 'city'
            await update.message.reply_text('Введите ваш город проживания:')
        elif step == 'city':
            context.user_data['city'] = text
            save_user_data(user_id, context.user_data['first_name'], context.user_data['last_name'], context.user_data['phone_number'], context.user_data['city'])
            del context.user_data['step']
            await welcome(update, context, new_registration=True)  # Отображение кнопки после регистрации
    elif 'awaiting_message' in context.user_data:
        context.user_data.pop('awaiting_message')
        save_message_to_sequence(user_id, text)
        await send_message_to_manager(update, context, text)

async def send_message_to_manager(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    user = update.message.from_user
    try:
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=f"Сообщение от пользователя {user.first_name} {user.last_name} (@{user.username}): {message}"
        )
        await update.message.reply_text("Ваше сообщение отправлено менеджеру. Ожидайте ответа.")
    except Exception as e:
        await update.message.reply_text("Ошибка при отправке сообщения менеджеру. Пожалуйста, попробуйте позже.")
        print(f"Error sending message to manager: {e}")

async def fort_boyard(update: Update, context: ContextTypes.DEFAULT_TYPE, use_hint=False):
    user_id = update.message.from_user.id
    stage, coins = load_fort_boyard_data(user_id)
    challenge = context.user_data['current_challenge'] if use_hint else get_random_challenge()

    if challenge:
        question = challenge["question"]
        options = challenge["options"]

        keyboard = [
            [InlineKeyboardButton(option, callback_data=f"challenge_{stage}_{option}")]
            for option in options
        ]
        keyboard.append([InlineKeyboardButton("Выйти из игры", callback_data=f"challenge_{stage}_exit")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.user_data['answer'] = challenge['answer']
        context.user_data['current_question'] = question
        context.user_data['current_options'] = options
        context.user_data['stage'] = stage
        context.user_data['current_challenge'] = challenge
        print(f"Fort Boyard: Stage {stage}, Question: {question}, Answer: {challenge['answer']}, Options: {options}")
        await update.message.reply_text(f"{question}", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Вы прошли все испытания! Поздравляем!")

async def fort_boyard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data.split("_")
    stage = int(data[1])
    selected_option = data[2]

    if selected_option == "exit":
        await query.message.delete()
        await query.message.reply_text("Вы вышли из игры.")
        # Обновляем клавиатуру после выхода из игры
        profile_data = load_user_profile(user_id)
        keyboard = [
            ["👤 Мой профиль", "🛒 Магазин"],
            ["ℹ️ О нас", "🏰 Пройти испытание"],
            ["🏆 Рейтинг игроков"],
            ["📞 Связаться с менеджером"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
        await context.bot.send_message(chat_id=query.message.chat_id, text="Теперь вы вышли из игры.", reply_markup=reply_markup)
        return

    print(f"Selected option (callback): {selected_option}")
    print(f"Expected stage: {stage}")
    print(f"Current stage in context: {context.user_data.get('stage')}")

    if selected_option == "retry":
        question = context.user_data.get('current_question')
        options = context.user_data.get('current_options')
        keyboard = [
            [InlineKeyboardButton(option, callback_data=f"challenge_{context.user_data['stage']}_{option}")]
            for option in options
        ]
        keyboard.append([InlineKeyboardButton("Выйти из игры", callback_data=f"challenge_{context.user_data['stage']}_exit")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"{question}", reply_markup=reply_markup)
    else:
        # Перезагружаем данные для текущего этапа
        challenge = context.user_data['current_challenge']
        correct_answer = challenge['answer']
        print(f"Selected option: {selected_option}")
        print(f"Correct answer: {correct_answer}")

        success, message, new_stage, coins = pass_challenge(user_id, selected_option, challenge)
        print(f"Challenge result: {success}")

        if success:
            context.user_data['stage'] = new_stage  # обновляем текущий этап в контексте
            correct_answers = context.user_data.get('correct_answers', 0) + 1
            context.user_data['correct_answers'] = correct_answers
            update_user_profile(user_id, correct_answers=correct_answers)
            await query.edit_message_text(message)
            await fort_boyard(query, context)  # автоматический переход к следующему испытанию
        else:
            keyboard = [
                [InlineKeyboardButton("Попробовать снова", callback_data=f"challenge_{stage}_retry")],
                [InlineKeyboardButton("Выйти из игры", callback_data=f"challenge_{stage}_exit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.delete()  # удаляет сообщение с неправильным ответом
            await query.message.reply_text("Неправильно. Готовы ли вы попробовать снова?", reply_markup=reply_markup)

async def show_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    stage, coins = load_fort_boyard_data(user_id)
    profile_data = load_user_profile(user_id)
    purchases = profile_data[5] if profile_data else ""

    if not isinstance(purchases, str):
        purchases = ""

    keyboard = []
    if "Скидка на игру" not in purchases:
        keyboard.append([InlineKeyboardButton("Скидка на игру (100 монет)", callback_data="shop_discount")])
    else:
        keyboard.append([InlineKeyboardButton("Скидка на игру (уже куплена)", callback_data="shop_discount")])
    keyboard.append([InlineKeyboardButton("Сувенир (50 монет)", callback_data="shop_souvenir")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Добро пожаловать в магазин! Ваш баланс: {coins} монет. Выберите товар для покупки:", reply_markup=reply_markup)

async def handle_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data.split("_")[1]
    stage, coins = load_fort_boyard_data(user_id)
    profile_data = load_user_profile(user_id)
    purchases = profile_data[5] if profile_data else ""

    if not isinstance(purchases, str):
        purchases = ""

    if choice == "discount":
        if "Скидка на игру" in purchases:
            await query.edit_message_text("Вы уже купили скидку на игру.")
        elif coins >= 100:
            coins -= 100
            save_fort_boyard_data(user_id, stage, coins)
            promo_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            purchases += f"Скидка на игру (Промокод: {promo_code}), "
            update_user_profile(user_id, purchases=purchases)
            await query.edit_message_text(f"Вы купили скидку на игру! Ваш промокод: {promo_code}. Покажите его менеджеру перед покупкой квеста.")
        else:
            await query.edit_message_text("У вас недостаточно монет для покупки скидки.")
    elif choice == "souvenir":
        if coins >= 50:
            coins -= 50
            save_fort_boyard_data(user_id, stage, coins)
            purchases += "Сувенир, "
            update_user_profile(user_id, purchases=purchases)
            await query.edit_message_text("Вы купили сувенир! Спасибо за покупку.")
    elif choice == "exit_game":
        await exit_game(update, context)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.first_name, users.last_name, fort_boyard.coins 
        FROM users 
        JOIN fort_boyard ON users.user_id = fort_boyard.user_id 
        ORDER BY fort_boyard.coins DESC 
        LIMIT 10
    """)
    leaderboard_data = cursor.fetchall()
    conn.close()

    leaderboard_text = "🏆 Топ 10 игроков:\n\n"
    for i, (first_name, last_name, coins) in enumerate(leaderboard_data):
        leaderboard_text += f"{i + 1}. {first_name} {last_name} - {coins} монет\n"

    await update.message.reply_text(leaderboard_text)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    profile_data = load_user_profile(user_id)

    if profile_data:
        first_name, last_name, phone_number, city, coins, purchases, correct_answers, fort_boyard_stage = profile_data
        purchases_text = purchases if purchases else "Нет покупок"
        profile_text = (
            f"👤 <b>Профиль пользователя</b>:\n\n"
            f"<b>Имя:</b> {first_name}\n"
            f"<b>Фамилия:</b> {last_name}\n"
            f"<b>Телефон:</b> {phone_number}\n"
            f"<b>Город:</b> {city}\n"
            f"<b>Монеты:</b> {coins}\n"
            f"<b>Покупки:</b> {purchases_text}\n"
            f"<b>Правильные ответы:</b> {correct_answers}\n"
            f"<b>Этап Форт Боярд:</b> {fort_boyard_stage}\n"
        )
    else:
        profile_text = "Профиль не найден."

    await update.message.reply_text(profile_text, parse_mode='HTML')

async def view_client_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, client_id: int):
    profile_data = load_user_profile(client_id)
    if profile_data:
        first_name, last_name, phone_number, city, coins, purchases, correct_answers, fort_boyard_stage = profile_data
        purchases_text = purchases if purchases else "Нет покупок"
        profile_text = (
            f"👤 <b>Профиль пользователя</b>:\n\n"
            f"<b>Имя:</b> {first_name}\n"
            f"<b>Фамилия:</b> {last_name}\n"
            f"<b>Телефон:</b> {phone_number}\n"
            f"<b>Город:</b> {city}\n"
            f"<b>Монеты:</b> {coins}\n"
            f"<b>Покупки:</b> {purchases_text}\n"
            f"<b>Правильные ответы:</b> {correct_answers}\n"
            f"<b>Этап Форт Боярд:</b> {fort_boyard_stage}\n"
        )
    else:
        profile_text = "Профиль не найден."
    await update.message.reply_text(profile_text, parse_mode='HTML')


async def use_hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "confirm_hint":
        stage, coins = load_fort_boyard_data(user_id)
        if stage == 0:
            await query.edit_message_text("Вы вышли из игры. Нажмите '🏰 Пройти испытание', чтобы продолжить.")
        elif coins >= 5:
            coins -= 5
            save_fort_boyard_data(user_id, stage, coins)
            hint = get_hint_for_challenge(context.user_data['current_challenge'])
            await query.edit_message_text(f"Подсказка для текущего испытания: {hint}")
            await fort_boyard(query, context, use_hint=True)  # Снова показать текущий вопрос
        else:
            await query.edit_message_text("У вас недостаточно монет для использования подсказки.")
    elif query.data == "cancel_hint":
        await query.edit_message_text("Использование подсказки отменено.")

async def exit_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data['stage'] = 0  # Обновляем стадию в контексте
    await query.message.reply_text("Игра завершена. Спасибо за игру!")
    # Обновляем клавиатуру после выхода из игры
    user_id = query.from_user.id
    profile_data = load_user_profile(user_id)
    keyboard = [
        ["👤 Мой профиль", "🛒 Магазин"],
        ["ℹ️ О нас", "🏰 Пройти испытание"],
        ["🏆 Рейтинг игроков"],
        ["📞 Связаться с менеджером"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    await context.bot.send_message(chat_id=query.message.chat_id, text="Теперь вы вышли из игры.", reply_markup=reply_markup)

async def contact_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    context.user_data['awaiting_message'] = True
    await update.message.reply_text("Свободный менеджер скоро с вами свяжется. Напишите ваше сообщение:")

async def handle_manager_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if text == "📋 Просмотр ожидающих сообщений":
        await view_pending_messages(update, context)
    elif text == "🔍 Просмотр профиля клиента":
        await update.message.reply_text("Введите ID клиента для просмотра его профиля:")
        context.user_data['awaiting_client_id'] = True
    elif text == "📊 Моя статистика":
        await view_manager_profile(update, context)
    elif 'awaiting_client_id' in context.user_data:
        client_id = int(text)
        await view_client_profile(update, context, client_id)
        del context.user_data['awaiting_client_id']

async def view_pending_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending_messages = load_pending_messages()
    if not pending_messages:
        await update.message.reply_text("Нет ожидающих сообщений от клиентов.")
        return

    keyboard = []
    for user_id, message in pending_messages:
        profile_data = load_user_profile(user_id)
        if profile_data:
            first_name, last_name, phone_number, city, coins, purchases, correct_answers, fort_boyard_stage = profile_data
            keyboard.append([InlineKeyboardButton(f"Ответить {first_name} {last_name}", callback_data=f"reply_{user_id}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите клиента, чтобы ответить:", reply_markup=reply_markup)

async def reply_to_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.data.split('_')[1])
    context.user_data['reply_to'] = user_id
    profile_data = load_user_profile(user_id)
    if profile_data:
        first_name, last_name, phone_number, city, coins, purchases, correct_answers, fort_boyard_stage = profile_data
        await query.message.reply_text(f"Напишите сообщение для пользователя {first_name} {last_name}:")

async def forward_message_to_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'reply_to' in context.user_data:
        user_id = context.user_data.pop('reply_to')
        try:
            print(f"Отправка сообщения пользователю {user_id}")
            print(f"Сообщение: {update.message.text}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"Сообщение от менеджера {manager_info['first_name']} {manager_info['last_name']}: {update.message.text}"
            )
            manager_stats['replies'] += 1
            await update.message.reply_text(f"Сообщение отправлено пользователю.")
            delete_message_from_sequence(user_id)  # Удаление сообщения из ожидающих после ответа
        except Exception as e:
            await update.message.reply_text(f"Ошибка при отправке сообщения клиенту: {e}")
            print(f"Error sending message to client: {e}")

async def view_manager_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    elapsed_time = datetime.now() - manager_stats['start_time']
    elapsed_time_str = str(timedelta(seconds=elapsed_time.seconds))  # Убираем миллисекунды
    profile_text = (
        f"👤 <b>Профиль менеджера</b>:\n\n"
        f"Имя: {manager_info['first_name']}\n"
        f"Фамилия: {manager_info['last_name']}\n"
        f"Количество ответов: {manager_stats['replies']}\n"
        f"Время работы: {elapsed_time_str}\n"
    )
    await update.message.reply_text(profile_text, parse_mode='HTML')

async def view_client_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, client_id: int):
    profile_data = load_user_profile(client_id)
    if profile_data:
        first_name, last_name, phone_number, city, coins, purchases, correct_answers, fort_boyard_stage = profile_data
        purchases_text = purchases if purchases else "Нет покупок"
        profile_text = (
            f"👤 <b>Профиль пользователя</b>:\n\n"
            f"<b>Имя:</b> {first_name}\n"
            f"<b>Фамилия:</b> {last_name}\n"
            f"<b>Телефон:</b> {phone_number}\n"
            f"<b>Город:</б> {city}\n"
            f"<b>Монеты:</б> {coins}\n"
            f"<b>Покупки:</б> {purchases_text}\n"
            f"<b>Правильные ответы:</б> {correct_answers}\n"
            f"<b>Этап Форт Боярд:</б> {fort_boyard_stage}\n"
        )
    else:
        profile_text = "Профиль не найден."
    await update.message.reply_text(profile_text, parse_mode='HTML')
