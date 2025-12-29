import telebot
import pymysql
import logging
from datetime import datetime, timedelta
from telebot import types
import atexit
import re
import time
import threading
import calendar

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
    7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# ---------------------- НАСТРОЙКИ ----------------------
TOKEN = "8099235929:AAHxfuiloTtJiju04W6NncPw_h-wtF8Szjs"
ADMIN_ID = 1914727710
ADMIN_PASSWORD = "111"
EMPLOYEES = [1914727710, 222222222,]  # ID сотрудников

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "kurs1111"
}

try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    print("Подключение к базе данных успешно.")
except Exception as e:
    print("Ошибка подключения к БД:", e)
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TOKEN)
user_states = {}

# Функция для закрытия соединения при выходе
def close_connection():
    cursor.close()
    conn.close()
    print("Соединение с БД закрыто.")

atexit.register(close_connection)

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================

def ensure_user_exists(user_id, username, first_name):
    """Добавляет пользователя в базу при первом взаимодействии"""
    try:
        query = """
            INSERT INTO users (id, username, first_name) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                username = VALUES(username),
                first_name = VALUES(first_name)
        """
        cursor.execute(query, (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя: {str(e)}")

def format_phone_number(phone):
    """Форматирование номера телефона для единообразия"""
    phone = re.sub(r'\D', '', phone)  # Удаляем все нецифровые символы
    if len(phone) == 11 and phone.startswith('8'):
        phone = '7' + phone[1:]
    return phone

def send_main_menu(chat_id, message_id=None):
    """Отправка/обновление главного меню"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('📋 Каталог кружков', callback_data='catalog')
    btn2 = types.InlineKeyboardButton('⭐ Мои записи', callback_data='my_bookings')
    btn3 = types.InlineKeyboardButton('💬 Поддержка', callback_data='support')
    btn4 = types.InlineKeyboardButton('🔍 Акции', callback_data='promotions')
    btn5 = types.InlineKeyboardButton('💡 Рекомендации', callback_data='recommendations')
    
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    text = '👋 *Добро пожаловать в HobbyGuide!*\n\nЗдесь вы можете найти кружок по своим интересам, посмотреть отзывы и узнать об акциях.\n\nВыберите действие:'
    
    if message_id:
        bot.edit_message_text(
            text,
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=markup
        )
    else:
        bot.send_message(
            chat_id,
            text,
            parse_mode='Markdown',
            reply_markup=markup
        )

# ====================== КЛИЕНТСКАЯ ЧАСТЬ ======================

@bot.message_handler(commands=['start'])
def main(message):
    # Добавляем пользователя в базу при старте
    ensure_user_exists(
        message.chat.id,
        message.from_user.username,
        message.from_user.first_name
    )
    send_main_menu(message.chat.id)

@bot.message_handler(commands=['admin'])
def admin_login(message):
    if message.chat.id not in EMPLOYEES:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к админ-панели.")
        return
    
    msg = bot.send_message(message.chat.id, "🔒 Введите пароль для доступа к админ-панели:")
    bot.register_next_step_handler(msg, process_admin_password)

def process_admin_password(message):
    if message.text == ADMIN_PASSWORD:
        user_states[message.chat.id] = "admin_logged_in"
        show_admin_panel(message.chat.id)
    else:
        bot.send_message(message.chat.id, "❌ Неверный пароль. Попробуйте снова.")

def show_admin_panel(chat_id, message_id=None):
    """Отображение админ-панели"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("➕ Добавить кружок", callback_data="admin_add_quest")
    btn2 = types.InlineKeyboardButton("📋 Управление кружками", callback_data="admin_manage_quests")
    btn3 = types.InlineKeyboardButton("🎁 Управление акциями", callback_data="admin_manage_promos")
    btn4 = types.InlineKeyboardButton("📅 Обработать заявки", callback_data="admin_bookings")
    btn5 = types.InlineKeyboardButton("📬 Вопросы поддержки", callback_data="admin_support")
    btn6 = types.InlineKeyboardButton("⭐ Управление отзывами", callback_data="admin_reviews")
    btn7 = types.InlineKeyboardButton("⬅ Выход", callback_data="back_main")

    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)

    text = "⚙ *Админ-панель*"
    
    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )

def show_catalog(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_dance = types.InlineKeyboardButton("💃 Танцы", callback_data="танцы")
    btn_drawing = types.InlineKeyboardButton("🎨 Рисование", callback_data="рисование")
    btn_pilates = types.InlineKeyboardButton("🧘 Пилатес", callback_data="пилатес")
    btn_yoga = types.InlineKeyboardButton("🧘 Йога", callback_data="йога")
    btn_sport = types.InlineKeyboardButton("⚽ Спорт", callback_data="спорт")
    btn_all = types.InlineKeyboardButton("📋 Все кружки", callback_data="all_circles")
    btn_main = types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
    
    markup.add(btn_dance, btn_drawing, btn_pilates, btn_yoga, btn_sport, btn_all, btn_main)
    
    text = "� *Выберите жанр или просмотрите все кружки:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def show_recommendations(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
    
    # Получаем все кружки для выбора рекомендаций
    query = "SELECT id, name FROM circles"
    cursor.execute(query)
    quests = cursor.fetchall()
    
    if not quests:
        markup.add(btn_back)
        text = "🔍 Рекомендации не найдены."
        
        if message_id:
            bot.edit_message_text(
                text,
                message.chat.id,
                message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )
        return
    
    for quest in quests:
        btn = types.InlineKeyboardButton(quest[1], callback_data=f"recommend_{quest[0]}")
        markup.add(btn)
    
    markup.add(btn_back)
    
    text = "💡 *Выберите кружок для рекомендаций товаров:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def show_recommendations_for_quest(message, quest_id, message_id=None):
    query = """
        SELECT 
            id, 
            name, 
            duration, 
            CONCAT(min_players, '-', max_players, ' человек') AS players_info, 
            difficulty, 
            price AS price_for_4, 
            address, 
            description AS legend,
            genre,
            image_url
        FROM circles 
        WHERE id=%s
    """
    cursor.execute(query, (quest_id,))
    quest = cursor.fetchone()
    
    if not quest:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="recommendations")
        markup.add(btn_back)
        text = "❌ Информация о кружке не найдена."
        if message_id:
            bot.edit_message_text(text, message.chat.id, message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    
    # Рекомендуемые товары
    query_products = "SELECT name, price, description FROM products WHERE quest_id=%s"
    cursor.execute(query_products, (quest_id,))
    products = cursor.fetchall()
    
    if not products:
        products_text = "Рекомендуемых товаров пока нет."
    else:
        products_text = "\n".join(f"• {p[0]} - {p[1]} руб.\n  {p[2]}" for p in products)
    
    text = (
        f"✨ *{quest[1]}*\n\n"
        f"🎉 {quest[7]}\n\n"
        f"⏰ *Длительность занятия:* {quest[2]} минут\n"
        f"👥 *Участников:* {quest[3]}-{quest[4]}\n"
        f"🎯 *Уровень подготовки:* {quest[5]}\n"
        f"💵 *Стоимость:* {quest[6]} руб. за занятие\n"
        f"📍 *Адрес:* {quest[7]}\n\n"
        f"🛒 *Рекомендуемые товары для этого кружка:*\n{products_text}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="recommendations")
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(text, message.chat.id, message_id, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

def show_genres(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_dance = types.InlineKeyboardButton("💃 Танцы", callback_data="танцы")
    btn_drawing = types.InlineKeyboardButton("🎨 Рисование", callback_data="рисование")
    btn_pilates = types.InlineKeyboardButton("🧘 Пилатес", callback_data="пилатес")
    btn_yoga = types.InlineKeyboardButton("🧘 Йога", callback_data="йога")
    btn_sport = types.InlineKeyboardButton("⚽ Спорт", callback_data="спорт")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="catalog")
    
    markup.add(btn_dance, btn_drawing, btn_pilates, btn_yoga, btn_sport, btn_back)
    
    text = "🎨 *Выберите жанр кружка:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def show_adult_genres(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_dance = types.InlineKeyboardButton("💃 Танцы", callback_data="quests_adults_танцы")
    btn_drawing = types.InlineKeyboardButton("🎨 Рисование", callback_data="quests_adults_рисование")
    btn_pilates = types.InlineKeyboardButton("🧘 Пилатес", callback_data="quests_adults_пилатес")
    btn_yoga = types.InlineKeyboardButton("🧘 Йога", callback_data="quests_adults_йога")
    btn_sport = types.InlineKeyboardButton("⚽ Спорт", callback_data="quests_adults_спорт")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="catalog")
    
    markup.add(btn_dance, btn_drawing, btn_pilates, btn_yoga, btn_sport, btn_back)
    
    text = "🎨 *Выберите жанр кружка для взрослых:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def show_quest_list(message, genre=None, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="catalog")
    
    # Фильтрация кружков по жанру
    quests = []
    query = "SELECT id, name, genre FROM circles"
    cursor.execute(query)
    all_quests = cursor.fetchall()
    
    for quest in all_quests:
        quest_id = quest[0]
        q_genre = quest[2]
        if genre:
            if q_genre == genre:
                quests.append((quest_id, quest[1]))
        else:
            quests.append((quest_id, quest[1]))
    
    if not quests:
        markup.add(btn_back)
        text = "🔍 Кружки не найдены."
        
        if message_id:
            bot.edit_message_text(
                text,
                message.chat.id,
                message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )
        return
    
    for quest in quests:
        btn = types.InlineKeyboardButton(quest[1], callback_data=f"quest_{quest[0]}")
        markup.add(btn)
    
    markup.add(btn_back)
    
    text = "🎯 *Выберите кружок:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def show_quest_info(message, quest_id, message_id=None):
    query = """
        SELECT 
            id, 
            name, 
            duration, 
            CONCAT(min_players, '-', max_players, ' человек') AS players_info, 
            difficulty, 
            price AS price_for_4, 
            address, 
            description AS legend,
            genre,
            image_url
        FROM circles 
        WHERE id=%s
    """
    cursor.execute(query, (quest_id,))
    quest = cursor.fetchone()
    
    if not quest:
        markup = types.InlineKeyboardMarkup()
        btn_catalog = types.InlineKeyboardButton("⬅ В каталог", callback_data="catalog")
        markup.add(btn_catalog)
        text = "❌ Информация о кружке не найдена."
        
        if message_id:
            bot.edit_message_text(
                text,
                message.chat.id,
                message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )
        return
    
    # Получаем тип и жанр из базы
    quest_type = "adults"
    quest_genre = quest[9]
    
    text = (
        f"✨ *{quest[1]}*\n\n"
        f"🎉 {quest[7]}\n\n"
        f"⏰ *Длительность занятия:* {quest[2]} минут\n"
        f"👥 *Размер группы:* {quest[3]}\n"
        f"🎯 *Уровень подготовки:* {quest[4]}\n"
        f"💵 *Стоимость:* {quest[5]} руб. за занятие\n"
        f"📍 *Адрес:* {quest[6]}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_book = types.InlineKeyboardButton("🗓 Записаться", callback_data=f"book_quest_{quest_id}")
    btn_reviews = types.InlineKeyboardButton("⭐ Отзывы", callback_data=f"quest_reviews_{quest_id}")
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="catalog")
    markup.add(btn_book, btn_reviews, btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def prompt_date_selection(message, quest_id, promo_id=None, message_id=None, year=None, month=None):
    today = datetime.today().date()
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    
    markup = types.InlineKeyboardMarkup()
    
    # Кнопки навигации по месяцам
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    prev_btn = types.InlineKeyboardButton("⬅", callback_data=f"calendar_{quest_id}_{prev_year}_{prev_month}_{promo_id or ''}")
    month_btn = types.InlineKeyboardButton(f"{MONTH_NAMES[month]} {year}", callback_data="noop")
    if next_year < 2026 or (next_year == 2026 and next_month <= 1):
        next_btn = types.InlineKeyboardButton("➡", callback_data=f"calendar_{quest_id}_{next_year}_{next_month}_{promo_id or ''}")
    else:
        next_btn = types.InlineKeyboardButton(" ", callback_data="noop")
    
    markup.row(prev_btn, month_btn, next_btn)
    
    # Дни недели
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(day, callback_data="noop") for day in days])
    
    # Календарь
    month_calendar = calendar.monthcalendar(year, month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="noop"))
            else:
                date_obj = datetime(year, month, day).date()
                if date_obj < today or (date_obj - today).days > 45:
                    row.append(types.InlineKeyboardButton(" ", callback_data="noop"))
                else:
                    callback_data = f"date_{quest_id}_{date_obj}"
                    if promo_id:
                        callback_data += f"_{promo_id}"
                    row.append(types.InlineKeyboardButton(str(day), callback_data=callback_data))
        markup.row(*row)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"back_date_{quest_id}")
    markup.row(btn_back)
    
    text = "📅 *Выберите дату для кружка:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def prompt_time_selection(message, quest_id, selected_date, promo_id=None, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=3)
    now = datetime.now()
    today = datetime.today().date()
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date() if isinstance(selected_date, str) else selected_date
    threshold = now + timedelta(hours=2) if selected_date_obj == today else None

    # Формируем временные слоты
    start = datetime.strptime("10:00", "%H:%M")
    end = datetime.strptime("22:00", "%H:%M")
    delta = timedelta(minutes=90)
    times = []
    current_slot = start
    
    while current_slot <= end:
        times.append(current_slot.strftime("%H:%M"))
        current_slot += delta

    available_found = False
    for t in times:
        slot_time = datetime.strptime(t, "%H:%M").time()
        slot_datetime = datetime.combine(selected_date_obj, slot_time)
        
        query = "SELECT COUNT(*) FROM bookings WHERE quest_id=%s AND date=%s AND time=%s AND status != 'cancelled'"
        cursor.execute(query, (int(quest_id), selected_date_obj, t))
        count = cursor.fetchone()[0]
        
        if selected_date_obj == today and slot_datetime < threshold:
            # Прошедший слот
            btn = types.InlineKeyboardButton(f"⏰ {t}", callback_data="noop")
        elif count == 0:
            # Свободный слот
            available_found = True
            callback_data = f"time_{quest_id}_{selected_date_obj}_{t}"
            if promo_id:
                callback_data += f"_{promo_id}"
            btn = types.InlineKeyboardButton(f"✅ {t}", callback_data=callback_data)
        else:
            # Занятый слот
            btn = types.InlineKeyboardButton(f"❌ {t}", callback_data="noop")
        markup.add(btn)
    
    if not available_found:
        markup.add(types.InlineKeyboardButton("😔 Нет свободных слотов", callback_data="noop"))
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"back_time_{quest_id}_{selected_date_obj}")
    markup.add(btn_back)
    
    text = "⏰ *Выберите время для занятия:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def prompt_players_selection(message, quest_id, selected_date, selected_time, promo_id=None, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # Получаем ограничения по игрокам для кружка
    query = "SELECT min_players, max_players FROM circles WHERE id=%s"
    cursor.execute(query, (quest_id,))
    min_players, max_players = cursor.fetchone()
    
    # Генерируем кнопки выбора количества игроков
    for i in range(min_players, max_players + 1):
        callback_data = f"players_{quest_id}_{selected_date}_{selected_time}_{i}"
        if promo_id:
            callback_data += f"_{promo_id}"
        btn = types.InlineKeyboardButton(
            f"👥 {i} игроков", 
            callback_data=callback_data
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton(
        "⬅ Назад", 
        callback_data=f"back_players_{quest_id}_{selected_date}_{selected_time}"
    )
    markup.add(btn_back)
    
    text = "👥 *Выберите количество игроков:*"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def confirm_booking_details(message, quest_id, selected_date, selected_time, players, promo_id=None, message_id=None):
    query = "SELECT name, duration, price, address, description FROM circles WHERE id=%s"
    cursor.execute(query, (quest_id,))
    quest = cursor.fetchone()
    
    if not quest:
        text = "❌ Ошибка получения данных кружка."
        if message_id:
            bot.edit_message_text(text, message.chat.id, message_id)
        else:
            bot.send_message(message.chat.id, text)
        return
    
    base_price = float(quest[2])
    players = int(players)
    
    # Расчет стоимости (фиксированная за занятие)
    total_price = base_price
        
    # Проверяем подписку на бонусы
    user_id = message.chat.id
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE user_id = %s", (user_id,))
    is_subscriber = cursor.fetchone()[0] > 0
    
    discount_text = ""
    promo_discount = 0.0
    
    # Применяем скидку по акции если есть
    if promo_id:
        try:
            cursor.execute("SELECT discount FROM promotions WHERE id=%s", (promo_id,))
            promo = cursor.fetchone()
            if promo:
                promo_discount = float(promo[0])
                total_price -= promo_discount
                discount_text += f"\n🎁 *Скидка по акции:* -{promo_discount:.2f} руб."
        except Exception as e:
            logging.error(f"Ошибка при применении скидки: {str(e)}")
    
    # Применяем скидку подписчика
    if is_subscriber:
        discount = total_price * 0.1  # 10% скидка
        total_price -= discount
        discount_text += f"\n🎁 *Скидка 10%:* -{discount:.2f} руб."

    text = (
        f"📝 *Детали записи*\n\n"
        f"🎮 *Кружок:* {quest[0]}\n"
        f"📅 *Дата:* {selected_date}\n"
        f"⏰ *Время:* {selected_time}\n"
        f"⏱ *Длительность:* {quest[1]} минут\n"
        f"📍 *Адрес:* {quest[3]}\n"
        f"📖 *Описание:* {quest[4]}\n"
        f"👥 *Участник:* 1\n"
        f"💵 *Стоимость:* {total_price:.2f} руб.{discount_text}\n\n"
        f"*Подтвердите запись:*"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_confirm = types.InlineKeyboardButton(
        "✅ Подтвердить запись", 
        callback_data=f"confirm|{quest_id}|{selected_date}|{selected_time}|1|nopre|{promo_id or ''}"
    )
    btn_recommend = types.InlineKeyboardButton("💡 Рекомендации товаров", callback_data=f"recommend_{quest_id}")
    btn_main = types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"back_time_{quest_id}_{selected_date}")
    
    markup.add(btn_confirm, btn_recommend)
    markup.row(btn_main, btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def complete_booking(call, quest_id, selected_date, selected_time, players, prepayment_flag, promo_id=None):
    # Добавляем пользователя в базу при бронировании
    ensure_user_exists(
        call.from_user.id,
        call.from_user.username,
        call.from_user.first_name
    )
    
    query = "INSERT INTO bookings (user_id, quest_id, date, time, players, prepayment, status) VALUES (%s, %s, %s, %s, %s, %s, 'pending')"
    prepayment = 1 if prepayment_flag == "pre" else 0
    
    try:
        cursor.execute(query, (call.from_user.id, quest_id, selected_date, selected_time, players, prepayment))
        conn.commit()
        booking_id = cursor.lastrowid
        
        # Получаем название кружка для уведомления
        cursor.execute("SELECT name FROM circles WHERE id=%s", (quest_id,))
        quest_name = cursor.fetchone()[0]
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_main = types.InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")
        btn_bookings = types.InlineKeyboardButton("⭐ Мои брони", callback_data="my_bookings")
        markup.add(btn_main, btn_bookings)
        
        bot.send_message(
            call.message.chat.id,
            "🎉 *Ваша бронь принята!*\n\nСкоро с вами свяжется администратор для подтверждения.",
            parse_mode='Markdown',
            reply_markup=markup
        )
        
        # Уведомление администратору
        admin_text = (
            f"🔔 *Новая бронь!*\n\n"
            f"🆔 *Номер брони:* #{booking_id}\n"
            f"👤 Пользователь: @{call.from_user.username or call.from_user.first_name}\n"
            f"🆔 ID: {call.from_user.id}\n"
            f"📞 Телеграм: [Написать](tg://user?id={call.from_user.id})\n"
            f"� Кружок: {quest_name}\n"
            f"📅 Дата: {selected_date}\n"
            f"⏰ Время: {selected_time}\n"
            f"👥 Участников: {players}\n"
            f"💳 Предоплата: {'Да' if prepayment else 'Нет'}"
        )
        
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Ошибка при бронировании: {str(e)}")
        try:
            bot.edit_message_text(
                "❌ Произошла ошибка при бронировании. Пожалуйста, попробуйте позже.",
                call.message.chat.id, 
                call.message.message_id
            )
        except:
            bot.send_message(
                call.message.chat.id,
                "❌ Произошла ошибка при бронировании. Пожалуйста, попробуйте позже."
            )

def show_bookings(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_upcoming = types.InlineKeyboardButton('📅 Предстоящие записи', callback_data='bookings_upcoming')
    btn_past = types.InlineKeyboardButton('📚 Прошедшие записи', callback_data='bookings_past')
    btn_refresh = types.InlineKeyboardButton('🔄 Обновить', callback_data='my_bookings')
    btn_back = types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_main')
    
    markup.add(btn_upcoming, btn_past)
    markup.add(btn_refresh, btn_back)
    
    text = '🌟 *Мои записи*\n\nВыберите категорию для просмотра ваших бронирований:'
    
    if message_id:
        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                pass  # Do nothing if the message is the same
            else:
                raise
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode='Markdown',
            reply_markup=markup
        )

def show_upcoming_bookings(message, message_id=None):
    today = datetime.today().date()
    query = """
        SELECT b.id, b.quest_id, b.date, b.time, b.players, b.prepayment, b.status, q.name, q.address, q.duration
        FROM bookings b 
        JOIN circles q ON b.quest_id = q.id 
        WHERE b.user_id = %s AND b.date >= %s AND b.status != 'cancelled'
        ORDER BY b.date ASC, b.time ASC
    """
    cursor.execute(query, (message.chat.id, today))
    bookings = cursor.fetchall()
    
    status_translation = {
        'pending': 'ожидает подтверждения',
        'confirmed': 'подтверждена',
        'completed': 'завершена'
    }
    
    if not bookings:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="my_bookings")
        markup.add(btn_back)
        
        text = "📭 У вас нет предстоящих записей."
        
        if message_id:
            try:
                bot.edit_message_text(text, message.chat.id, message_id, reply_markup=markup)
            except telebot.apihelper.ApiTelegramException as e:
                if "message is not modified" in str(e):
                    pass
                else:
                    raise
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    
    msg = "📅 *Предстоящие записи:*\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for i, booking in enumerate(bookings, 1):
        booking_id, quest_id, date, time_slot, players, prepayment, status, quest_name, address, duration = booking
        status_text = status_translation.get(status, status)
        status_icon = "🟢" if status == 'confirmed' else "🟡" if status == 'pending' else "🔴"
        
        booking_date = date if isinstance(date, datetime) else datetime.strptime(str(date), '%Y-%m-%d').date()
        days_until = (booking_date - today).days
        
        msg += f"{i}. {status_icon} *{quest_name}*\n📅 {date} ⏰ {time_slot}\n\n"
        
        # Кнопка для просмотра деталей этой записи
        btn_view = types.InlineKeyboardButton(f"📋 Запись {i}", callback_data=f"view_booking_{booking_id}")
        markup.add(btn_view)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="my_bookings")
    markup.add(btn_back)
    
    if message_id:
        try:
            bot.edit_message_text(msg, message.chat.id, message_id, parse_mode="Markdown", reply_markup=markup)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
    else:
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

def show_past_bookings(message, message_id=None):
    today = datetime.today().date()
    query = """
        SELECT b.id, b.quest_id, b.date, b.time, b.players, b.prepayment, b.status, q.name, q.address, q.duration
        FROM bookings b 
        JOIN circles q ON b.quest_id = q.id 
        WHERE b.user_id = %s AND b.date < %s
        ORDER BY b.date DESC, b.time DESC
    """
    cursor.execute(query, (message.chat.id, today))
    bookings = cursor.fetchall()
    
    status_translation = {
        'pending': 'ожидает подтверждения',
        'confirmed': 'подтверждена',
        'cancelled': 'отменена',
        'completed': 'завершена'
    }
    
    if not bookings:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="my_bookings")
        markup.add(btn_back)
        
        text = "📭 У вас нет прошедших записей."
        
        if message_id:
            bot.edit_message_text(text, message.chat.id, message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
        return
    
    msg = "📚 *Прошедшие записи:*\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for i, booking in enumerate(bookings, 1):
        booking_id, quest_id, date, time_slot, players, prepayment, status, quest_name, address, duration = booking
        status_text = status_translation.get(status, status)
        status_icon = "🟢" if status == 'confirmed' else "🟡" if status == 'pending' else "🔴" if status == 'cancelled' else "✅"
        
        msg += f"{i}. {status_icon} *{quest_name}*\n📅 {date} ⏰ {time_slot}\n\n"
        
        # Кнопка для просмотра деталей этой записи
        btn_view = types.InlineKeyboardButton(f"📋 Запись {i}", callback_data=f"view_booking_{booking_id}")
        markup.add(btn_view)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="my_bookings")
    markup.add(btn_back)
    
    if message_id:
        try:
            bot.edit_message_text(msg, message.chat.id, message_id, parse_mode="Markdown", reply_markup=markup)
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise
    else:
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

def show_booking_detail(message, booking_id, message_id=None):
    query = """
        SELECT 
            b.id, b.quest_id, b.date, b.time, b.players, b.prepayment, b.status, 
            q.name, u.first_name, u.username, u.id as user_id, q.address, q.duration, q.price, q.description
        FROM bookings b 
        JOIN circles q ON b.quest_id = q.id 
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s
    """
    cursor.execute(query, (booking_id,))
    booking = cursor.fetchone()
    
    if not booking:
        text = "❌ Запись не найдена."
        if message_id:
            bot.edit_message_text(text, message.chat.id, message_id)
        else:
            bot.send_message(message.chat.id, text)
        return
    
    booking_id = booking[0]
    quest_id = booking[1]
    date = booking[2]
    time_slot = booking[3]
    players = booking[4]
    status = booking[6]
    quest_name = booking[7]
    first_name = booking[8]
    username = booking[9]
    user_id = booking[10]
    address = booking[11]
    duration = booking[12]
    price = booking[13]
    description = booking[14]
    
    # Статусы на русском
    status_translation = {
        'pending': 'ожидает подтверждения',
        'confirmed': 'подтверждена',
        'cancelled': 'отменена',
        'completed': 'завершена'
    }
    status_text = status_translation.get(status, status)
    
    status_icon = "🟢" if status == 'confirmed' else "🟡" if status == 'pending' else "🔴" if status == 'cancelled' else "✅"
    prepayment = "✅ Да" if booking[5] else "❌ Нет"
    
    # Расчет стоимости
    total_price = float(price)
    
    # Проверяем подписку на бонусы
    cursor.execute("SELECT COUNT(*) FROM subscribers WHERE user_id = %s", (user_id,))
    is_subscriber = cursor.fetchone()[0] > 0
    
    discount_text = ""
    if is_subscriber:
        discount = total_price * 0.1  # 10% скидка
        total_price -= discount
        discount_text = f" (скидка 10%: -{discount:.0f} руб.)"
    
    text = (
        f"{status_icon} *Детали записи №{booking_id}*\n\n"
        f"🎨 *Кружок:* {quest_name}\n"
        f"📖 *Описание:* {description}\n"
        f"👤 *Клиент:* {first_name} (@{username if username else 'без username'})\n"
        f"📅 *Дата:* {date}\n"
        f"⏰ *Время:* {time_slot} ({duration} мин)\n"
        f"📍 *Адрес:* {address}\n"
        f"👥 *Участник:* 1\n"
        f"💳 *Предоплата:* {prepayment}\n"
        f"💵 *Стоимость:* {total_price:.0f} руб.{discount_text}\n"
        f"🔄 *Статус записи:* {status_text}\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    today = datetime.today().date()
    booking_date = date if isinstance(date, datetime) else datetime.strptime(str(date), '%Y-%m-%d').date()
    delta = booking_date - today
    
    if delta >= timedelta(days=1) and status != 'cancelled':
        btn_edit = types.InlineKeyboardButton("✏️ Изменить", callback_data=f"edit_booking_{booking_id}")
        btn_cancel = types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_booking_{booking_id}")
        markup.row(btn_edit, btn_cancel)
    
    btn_contact = types.InlineKeyboardButton("☎ Связаться", callback_data=f"contact_{booking_id}")
    markup.add(btn_contact)
    
    if booking_date < today and status not in ('cancelled'):
        # Проверяем, оставлял ли пользователь отзыв на эту запись
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE booking_id = %s", (booking_id,))
        review_exists = cursor.fetchone()[0] == 0
        
        if review_exists:
            btn_review = types.InlineKeyboardButton("⭐ Оставить отзыв", callback_data=f"review_{booking_id}")
            markup.add(btn_review)
    
    # Кнопки навигации
    if delta >= 0:
        btn_back = types.InlineKeyboardButton("⬅ К предстоящим", callback_data="bookings_upcoming")
    else:
        btn_back = types.InlineKeyboardButton("⬅ К прошедшим", callback_data="bookings_past")
    
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def process_cancel_booking(message, booking_id):
    query = "SELECT date, status, quest_id FROM bookings WHERE id=%s AND user_id=%s"
    cursor.execute(query, (booking_id, message.chat.id))
    result = cursor.fetchone()
    
    if not result:
        bot.answer_callback_query(message.id if hasattr(message, 'id') else None, "❌ Запись не найдена.")
        return
    
    booking_date, status, quest_id = result
    today = datetime.today().date()
    
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
    
    if status == "cancelled":
        bot.send_message(message.chat.id, "ℹ️ Запись уже отменена.")
        return
    
    # Получаем название кружка
    cursor.execute("SELECT name FROM circles WHERE id=%s", (quest_id,))
    quest_name = cursor.fetchone()[0]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_cancel_{booking_id}")
    btn_no = types.InlineKeyboardButton("❌ Нет", callback_data=f"booking_{booking_id}")
    markup.add(btn_yes, btn_no)
    
    text = f"❓ Вы действительно хотите отменить запись на *{quest_name}* на {booking_date}?"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

def quick_cancel_booking(message, booking_id):
    query = "SELECT date, status, quest_id FROM bookings WHERE id=%s AND user_id=%s"
    cursor.execute(query, (booking_id, message.chat.id))
    result = cursor.fetchone()
    
    if not result:
        bot.answer_callback_query(message.id if hasattr(message, 'id') else None, "❌ Запись не найдена.")
        return
    
    booking_date, status, quest_id = result
    today = datetime.today().date()
    
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
    
    if (booking_date - today).days < 1:
        bot.send_message(message.chat.id, "⛔ Отменить запись можно только за 1 день до начала.")
        return
    
    if status == "cancelled":
        bot.send_message(message.chat.id, "ℹ️ Запись уже отменена.")
        return
    
    # Получаем название кружка
    cursor.execute("SELECT name FROM circles WHERE id=%s", (quest_id,))
    quest_name = cursor.fetchone()[0]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Да, отменить", callback_data=f"confirm_quick_cancel_{booking_id}")
    btn_no = types.InlineKeyboardButton("❌ Нет", callback_data="bookings_upcoming")
    markup.add(btn_yes, btn_no)
    
    text = f"❓ Вы действительно хотите отменить запись на *{quest_name}* на {booking_date}?"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

def finalize_quick_cancel_booking(message, booking_id):
    try:
        # Получаем информацию о записи для уведомления
        query = """
            SELECT b.quest_id, b.date, b.time, q.name, 
                   u.first_name, u.username, u.id as user_id
            FROM bookings b
            JOIN circles q ON b.quest_id = q.id
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        booking_info = cursor.fetchone()
        
        if booking_info:
            quest_id, date, time_slot, quest_name, first_name, username, user_id = booking_info
        
        query = "UPDATE bookings SET status='cancelled' WHERE id=%s"
        cursor.execute(query, (booking_id,))
        conn.commit()
        
        bot.send_message(
            message.chat.id,
            "✅ Ваша запись **отменена**.",
            parse_mode="Markdown"
        )
        
        # Уведомление администратору
        if booking_info:
            admin_text = (
                f"⚠️ *Отмена записи!*\n\n"
                f"🆔 *Номер записи:* #{booking_id}\n"
                f"👤 Пользователь: {first_name} (@{username or 'без username'})\n"
                f"🆔 ID: {user_id}\n"
                f"📞 Телеграм: [Написать](tg://user?id={user_id})\n"
                f"🎨 Кружок: {quest_name}\n"
                f"📅 Дата: {date}\n"
                f"⏰ Время: {time_slot}\n"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
            
        # Обновляем список
        time.sleep(1)
        show_upcoming_bookings(message)
        
    except Exception as e:
        logging.error(f"Ошибка при быстрой отмене записи: {str(e)}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при отмене записи.")

def finalize_cancel_booking(message, booking_id):
    try:
        # Получаем информацию о брони для уведомления
        query = """
            SELECT b.quest_id, b.date, b.time, q.name, 
                   u.first_name, u.username, u.id as user_id
            FROM bookings b
            JOIN circles q ON b.quest_id = q.id
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        booking_info = cursor.fetchone()
        
        if booking_info:
            quest_id, date, time_slot, quest_name, first_name, username, user_id = booking_info
        
        query = "UPDATE bookings SET status='cancelled' WHERE id=%s"
        cursor.execute(query, (booking_id,))
        conn.commit()
        
        try:
            bot.edit_message_text(
                "✅ Ваша бронь **отменена**.",
                message.chat.id, 
                message.message_id, 
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                message.chat.id,
                "✅ Ваша бронь **отменена**.",
                parse_mode="Markdown"
            )
        
        # Уведомление администратору
        if booking_info:
            admin_text = (
                f"⚠️ *Отмена записи!*\n\n"
                f"🆔 *Номер записи:* #{booking_id}\n"
                f"👤 Пользователь: {first_name} (@{username or 'без username'})\n"
                f"🆔 ID: {user_id}\n"
                f"📞 Телеграм: [Написать](tg://user?id={user_id})\n"
                f"🎨 Кружок: {quest_name}\n"
                f"📅 Дата: {date}\n"
                f"⏰ Время: {time_slot}\n"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Ошибка при отмене брони: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при отмене брони."
        )

def edit_booking_date(message, booking_id):
    markup = types.InlineKeyboardMarkup(row_width=3)
    today = datetime.today().date()
    
    for i in range(21):
        day = today + timedelta(days=i)
        btn = types.InlineKeyboardButton(
            day.strftime("%d.%m"), 
            callback_data=f"edit_date_{booking_id}_{day}"
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"booking_{booking_id}")
    markup.add(btn_back)
    
    bot.send_message(
        message.chat.id,
        "📅 *Выберите новую дату для брони:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

def edit_booking_time_selection(message, booking_id, new_date):
    markup = types.InlineKeyboardMarkup(row_width=3)
    start = datetime.strptime("10:00", "%H:%M")
    end = datetime.strptime("22:00", "%H:%M")
    delta = timedelta(minutes=90)
    times = []
    current = start
    
    while current <= end:
        times.append(current.strftime("%H:%M"))
        current += delta
    
    available_found = False
    query = "SELECT quest_id FROM bookings WHERE id=%s"
    cursor.execute(query, (booking_id,))
    result = cursor.fetchone()
    
    if not result:
        try:
            bot.edit_message_text("❌ Ошибка: бронь не найдена.", message.chat.id, message.message_id)
        except:
            bot.send_message(message.chat.id, "❌ Ошибка: бронь не найдена.")
        return
    
    quest_id = result[0]
    
    for t in times:
        query = "SELECT COUNT(*) FROM bookings WHERE quest_id=%s AND date=%s AND time=%s AND status != 'cancelled' AND id != %s"
        cursor.execute(query, (quest_id, new_date, t, booking_id))
        count = cursor.fetchone()[0]
        
        if count == 0:
            available_found = True
            btn = types.InlineKeyboardButton(t, callback_data=f"edit_time_{booking_id}_{new_date}_{t}")
            markup.add(btn)
    
    if not available_found:
        markup.add(types.InlineKeyboardButton("😔 Нет свободных слотов", callback_data="noop"))
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"edit_booking_{booking_id}")
    markup.add(btn_back)
    
    bot.send_message(
        message.chat.id,
        "⏰ *Выберите новое время для брони:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

def finalize_edit_booking(message, booking_id, new_date, new_time):
    try:
        # Получаем старую информацию о брони
        query = """
            SELECT b.quest_id, b.date, b.time, q.name, 
                   u.first_name, u.username, u.id as user_id
            FROM bookings b
            JOIN circles q ON b.quest_id = q.id
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        old_booking_info = cursor.fetchone()
        
        if old_booking_info:
            quest_id, old_date, old_time, quest_name, first_name, username, user_id = old_booking_info
        
        query = "UPDATE bookings SET date=%s, time=%s WHERE id=%s"
        cursor.execute(query, (new_date, new_time, booking_id))
        conn.commit()
        
        try:
            bot.edit_message_text(
                "✅ Ваша бронь успешно **изменена**!",
                message.chat.id, 
                message.message_id, 
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                message.chat.id,
                "✅ Ваша бронь успешно **изменена**!",
                parse_mode="Markdown"
            )
        
        # Уведомление администратору
        if old_booking_info:
            admin_text = (
                f"ℹ️ *Изменение записи!*\n\n"
                f"🆔 *Номер записи:* #{booking_id}\n"
                f"👤 Пользователь: {first_name} (@{username or 'без username'})\n"
                f"🆔 ID: {user_id}\n"
                f"📞 Телеграм: [Написать](tg://user?id={user_id})\n"
                f"🎨 Кружок: {quest_name}\n\n"
                f"📅 *Старая дата:* {old_date}\n"
                f"⏰ *Старое время:* {old_time}\n\n"
                f"📅 *Новая дата:* {new_date}\n"
                f"⏰ *Новое время:* {new_time}"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        
        # Обновляем список бронирований
        time.sleep(1)
        show_bookings(message)
        
    except Exception as e:
        logging.error(f"Ошибка при изменении брони: {str(e)}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при изменении брони."
        )

def show_promotions(message, message_id=None):
    query = "SELECT id, name, end_date FROM promotions WHERE end_date >= CURDATE() ORDER BY end_date ASC"
    cursor.execute(query)
    promotions = cursor.fetchall()
    
    if not promotions:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Главное меню", callback_data="back_main")
        markup.add(btn_back)
        
        text = "🎯 На данный момент акций нет."
        
        if message_id:
            bot.edit_message_text(
                text,
                message.chat.id,
                message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )
        return

    text = "🎉 *Текущие акции:*\n\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for promo in promotions:
        promo_id = promo[0]
        title = promo[1]
        valid_until = promo[2]
        
        text += f"• **{title}** (до {valid_until})\n"
        btn = types.InlineKeyboardButton(
            f"🔍 {title}", 
            callback_data=f"promo_{promo_id}"
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Главное меню", callback_data="back_main")
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def show_promotion_detail(message, promo_id, message_id=None):
    query = "SELECT title, description, discount, quest_id, valid_until FROM promotions WHERE id=%s"
    cursor.execute(query, (promo_id,))
    promo = cursor.fetchone()
    
    if not promo:
        text = "❌ Акция не найдена."
        if message_id:
            bot.edit_message_text(text, message.chat.id, message_id)
        else:
            bot.send_message(message.chat.id, text)
        return
    
    title, description, discount, quest_id, valid_until = promo
    text = (
        f"🎁 *{title}*\n\n"
        f"{description}\n\n"
        f"💸 *Скидка:* {discount} руб.\n"
        f"📅 *Действует до:* {valid_until}"
    )
    
    markup = types.InlineKeyboardMarkup()
    
    if quest_id:
        btn_book = types.InlineKeyboardButton(
            "🗓 Записаться на кружок с акцией", 
            callback_data=f"bookpromo_{quest_id}_{promo_id}"
        )
        markup.add(btn_book)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="promotions")
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

# ===================== РАЗДЕЛ ПОДДЕРЖКИ =====================

def support_menu(message, message_id=None):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_about = types.InlineKeyboardButton("ℹ О нас", callback_data="support_about")
    btn_contacts = types.InlineKeyboardButton("📞 Контакты", callback_data="support_contacts")
    btn_faq = types.InlineKeyboardButton("❓ FAQ", callback_data="support_faq")
    btn_ask = types.InlineKeyboardButton("💬 Задать вопрос", callback_data="support_ask")
    btn_reviews = types.InlineKeyboardButton("⭐ Отзывы", callback_data="support_reviews")
    btn_tips = types.InlineKeyboardButton("💡 Советы", callback_data="support_tips")
    btn_rules = types.InlineKeyboardButton("⚠ Правила", callback_data="support_rules")
    btn_bonus = types.InlineKeyboardButton("🎁 Бонусы", callback_data="support_bonus")
    btn_back = types.InlineKeyboardButton("⬅ Главное меню", callback_data="back_main")
    
    markup.add(
        btn_about, btn_contacts,
        btn_faq, btn_ask,
        btn_reviews, btn_tips,
        btn_rules, btn_bonus,
        btn_back
    )
    
    text = "🔹 *Раздел поддержки*\n\nВыберите нужный пункт:"
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def support_about(message, message_id=None):
    text = (
        "🏠 *О HobbyGuide*\n\n"
        "Мы – ваш надежный помощник в мире хобби и творчества! 🎨\n\n"
        "Наши кружки предлагают:\n"
        "✨ Разнообразие занятий по интересам\n"
        "🧩 Развитие навыков и талантов\n"
        "🎭 Творческую атмосферу\n"
        "😍 Радость от любимого дела\n\n"
        "Присоединяйтесь к нашим кружкам и откройте для себя новые горизонты!"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def support_contacts(message, message_id=None):
    text = (
        "📍 *Контактная информация*\n\n"
        "🏠 Адрес: ул. Творческая, 15, Москва\n"
        "📞 Телефон: +7 (999) 123-45-67\n"
        "🌐 Сайт: [hobbyguide.ru](https://hobbyguide.ru)\n"
        "✉ Email: support@hobbyguide.ru\n\n"
        "⏰ *Часы работы:*\n"
        "Пн-Пт: 9:00 - 21:00\n"
        "Сб-Вс: 10:00 - 20:00\n\n"
        "Мы всегда рады помочь с выбором кружка! 😊"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_back)
    
    if message_id:
        bot.edit_message_text(
            text,
            message.chat.id,
            message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    else:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def support_faq(message):
    """FAQ: Часто задаваемые вопросы"""
    text = (
        "❓ *FAQ: Часто задаваемые вопросы*\n\n"
        "1. *Как записаться на кружок?*\n"
        "Выберите кружок в каталоге, затем укажите дату, время и количество участников.\n\n"
        "2. *Можно ли изменить запись?*\n"
        "Да, в разделе 'Мои записи' вы можете изменить или отменить запись за 1 день до занятия.\n\n"
        "3. *Какие кружки предлагаются?*\n"
        "Мы предлагаем кружки по танцам, рисованию, пилатесу, йоге и спорту для разных уровней.\n\n"
        "4. *Что делать, если мы опоздаем?*\n"
        "При опоздании более чем на 10 минут время занятия сокращается.\n\n"
        "5. *Есть ли возрастные ограничения?*\n"
        "Некоторые кружки имеют возрастные рекомендации. Уточняйте в описании кружка."
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text,
            message.chat.id,
            message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def support_ask(message):
    msg = bot.send_message(
        message.chat.id, 
        "✍ Напишите ваш вопрос, и администратор ответит вам!\n\n"
        "Максимальная длина сообщения - 1000 символов."
    )
    bot.register_next_step_handler(msg, process_support_question)

def process_support_question(message):
    if len(message.text) > 1000:
        bot.send_message(
            message.chat.id, 
            "❌ Сообщение слишком длинное. Максимум 1000 символов."
        )
        return
        
    user_id = message.chat.id
    question_text = message.text
    
    # Добавляем пользователя в базу
    ensure_user_exists(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    try:
        query = "INSERT INTO support_messages (user_id, message) VALUES (%s, %s)"
        cursor.execute(query, (user_id, question_text))
        conn.commit()
        
        bot.send_message(
            message.chat.id, 
            "✅ Ваш вопрос отправлен администратору. Ожидайте ответа!"
        )
        
        # Уведомление администратору
        admin_text = (
            f"📩 Новый вопрос от {message.from_user.first_name} (ID: {user_id}):\n\n"
            f"{question_text}\n\n"
            f"Для ответа используйте команду /admin"
        )
        bot.send_message(ADMIN_ID, admin_text)
        
    except Exception as e:
        logging.error(f"Ошибка при сохранении вопроса: {str(e)}")
        bot.send_message(
            message.chat.id, 
            "❌ Произошла ошибка при отправке вопроса. Пожалуйста, попробуйте позже."
        )

def support_reviews(message):
    """Показать последние отзывы"""
    query = """
        SELECT r.id, r.review, u.first_name, r.created_at 
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 10
    """
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    if not reviews:
        text = "⭐ Пока нет отзывов. Будьте первым!"
    else:
        text = "⭐ *Последние отзывы:*\n\n"
        for review in reviews:
            review_id, review_text, user_name, created_at = review
            text += f"👤 *{user_name}*:\n{review_text}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("📝 Оставить отзыв", callback_data="support_add_review")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_add, btn_back)
    
    try:
        bot.edit_message_text(
            text,
            message.chat.id,
            message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def support_add_review(message):
    msg = bot.send_message(
        message.chat.id, 
        "📝 Напишите ваш отзыв о нашем сервисе:\n\n"
        "Максимальная длина - 500 символов."
    )
    bot.register_next_step_handler(msg, process_support_review)

def process_support_review(message):
    if len(message.text) > 500:
        bot.send_message(
            message.chat.id, 
            "❌ Отзыв слишком длинный. Максимум 500 символов."
        )
        return
        
    user_id = message.chat.id
    review_text = message.text
    
    # Добавляем пользователя в базу
    ensure_user_exists(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    try:
        query = "INSERT INTO reviews (user_id, review, created_at) VALUES (%s, %s, NOW())"
        cursor.execute(query, (user_id, review_text))
        conn.commit()
        
        bot.send_message(
            message.chat.id, 
            "✅ Спасибо! Ваш отзыв сохранён."
        )
        
        # Уведомление администратору
        bot.send_message(
            ADMIN_ID, 
            f"⭐ Новый отзыв от {message.from_user.first_name} (ID: {user_id}):\n\n{review_text}"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при сохранении отзыва: {str(e)}")
        bot.send_message(
            message.chat.id, 
            "❌ Произошла ошибка при сохранении отзыва."
        )

def support_tips(message):
    """Советы по выбору кружков"""
    text = (
        "💡 *Советы по выбору кружков:*\n\n"
        "🎨 Определите свои интересы – танцы, рисование или спорт?\n"
        "🔦 Читайте отзывы – опыт других поможет сделать выбор\n"
        "⏳ Учитывайте расписание – регулярные занятия важны для прогресса\n"
        "🗝 Попробуйте пробное занятие – многие кружки предлагают бесплатные пробы\n"
        "🧠 Общайтесь с инструкторами – задавайте вопросы о программе"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def support_rules(message):
    """Правила посещения кружков"""
    text = (
        "⚠️ *Правила посещения кружков:*\n\n"
        "🚫 Соблюдайте чистоту – убирайте за собой материалы\n"
        "📵 Выключите телефоны – сосредоточьтесь на занятии\n"
        "🗣 Следуйте указаниям инструктора – это поможет достичь лучших результатов\n"
        "👥 Уважайте других участников – вместе заниматься намного приятнее\n"
        "⏰ Приходите вовремя – чтобы не мешать группе и инструктору"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def support_bonus(message):
    """Специальные бонусы"""
    text = (
        "🎁 *Специальные бонусы*\n\n"
        "Хотите получать эксклюзивные скидки и персональные предложения?\n\n"
        "🔔 Подпишитесь на наши новости и получите:\n"
        "• Скидку 10% на первое занятие\n"
        "• Уведомления о новых кружках\n"
        "• Специальные предложения в ваш день рождения\n"
        "• Участие в мастер-классах и мероприятиях"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_subscribe = types.InlineKeyboardButton("🔔 Подписаться", callback_data="support_subscribe")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="support_menu")
    markup.add(btn_subscribe, btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "support_subscribe")
def handle_support_subscribe(call):
    try:
        user_id = call.from_user.id
        query = "INSERT IGNORE INTO subscribers (user_id, first_name) VALUES (%s, %s)"
        cursor.execute(query, (user_id, call.from_user.first_name))
        conn.commit()
        
        bot.answer_callback_query(
            call.id,
            "✅ Вы успешно подписались на рассылку!",
            show_alert=True
        )
        
        # Отправляем бонус
        bot.send_message(
            call.message.chat.id,
            "🎉 *Спасибо за подписку!*\n\n"
            "Ваш бонус: скидка 10% на первое занятие. "
            "Просто сообщите администратору о вашей подписке при записи.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Ошибка при подписке: {str(e)}")
        bot.answer_callback_query(
            call.id,
            "❌ Произошла ошибка при подписке",
            show_alert=True
        )

def prompt_contact_admin(message, booking_id):
    msg = bot.send_message(
        message.chat.id, 
        "✉ Напишите ваше сообщение для администратора. Оно будет отправлено, и с вами свяжутся!\n\n"
        "Максимальная длина - 500 символов."
    )
    bot.register_next_step_handler(msg, process_contact_message, booking_id)

def process_contact_message(message, booking_id):
    if len(message.text) > 500:
        bot.send_message(
            message.chat.id, 
            "❌ Сообщение слишком длинное. Максимум 500 символов."
        )
        return
        
    user_info = f"{message.from_user.first_name} (ID: {message.from_user.id})"
    admin_text = (
        f"📩 *Сообщение от {user_info} по брони №{booking_id}:*\n\n"
        f"{message.text}"
    )
    
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    bot.send_message(
        message.chat.id, 
        "✅ Ваше сообщение отправлено. Администратор свяжется с вами!"
    )

def booking_review(message, booking_id):
    """Запрос отзыва о конкретной брони"""
    prompt_text = f"⭐ Напишите, пожалуйста, ваш отзыв о брони №{booking_id}:\n\nМаксимальная длина - 500 символов."
    msg = bot.send_message(message.chat.id, prompt_text)
    bot.register_next_step_handler(msg, process_booking_review, booking_id)

def process_booking_review(message, booking_id):
    """Сохранение отзыва о брони"""
    if len(message.text) > 500:
        bot.send_message(
            message.chat.id, 
            "❌ Отзыв слишком длинный. Максимум 500 символов."
        )
        return
        
    user_id = message.chat.id
    review_text = message.text
    
    # Добавляем пользователя в базу
    ensure_user_exists(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    try:
        # Получаем quest_id из брони
        query = "SELECT quest_id FROM bookings WHERE id = %s"
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        
        if result:
            quest_id = result[0]
            query = "INSERT INTO reviews (user_id, booking_id, review, created_at) VALUES (%s, %s, %s, NOW())"
            cursor.execute(query, (user_id, booking_id, review_text))
            conn.commit()
            
            bot.send_message(
                message.chat.id, 
                "✅ Спасибо! Ваш отзыв сохранён."
            )
            
            # Уведомление администратору
            bot.send_message(
                ADMIN_ID, 
                f"⭐ Новый отзыв от {message.from_user.first_name} (ID: {user_id}) по брони №{booking_id}:\n\n{review_text}"
            )
        
    except Exception as e:
        logging.error(f"Ошибка при сохранении отзыва: {str(e)}")
        bot.send_message(
            message.chat.id, 
            "❌ Произошла ошибка при сохранении отзыва."
        )

def show_quest_reviews(message, quest_id):
    """Показать отзывы о кружке"""
    query = """
        SELECT r.id, r.review, u.first_name, r.created_at 
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.quest_id = %s
        ORDER BY r.created_at DESC
        LIMIT 10
    """
    cursor.execute(query, (quest_id,))
    reviews = cursor.fetchall()
    
    if not reviews:
        text = "⭐ Пока нет отзывов об этом кружке. Будьте первым!"
    else:
        text = "⭐ *Отзывы об этом кружке:*\n\n"
        for review in reviews:
            review_id, review_text, user_name, created_at = review
            text += f"👤 *{user_name}*:\n{review_text}\n\n"
    
    markup = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("📝 Оставить отзыв", callback_data=f"quest_add_review_{quest_id}")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"quest_{quest_id}")
    markup.add(btn_add, btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

# ===================== АДМИНСКАЯ ПАНЕЛЬ =====================

def add_quest_start(message):
    msg = bot.send_message(message.chat.id, "✍ Введите название кружка:")
    bot.register_next_step_handler(msg, process_quest_name)

def process_quest_name(message):
    quest_data = {"name": message.text}
    msg = bot.send_message(message.chat.id, "📝 Введите краткое описание кружка:")
    bot.register_next_step_handler(msg, process_quest_description, quest_data)

def process_quest_description(message, quest_data):
    quest_data["description"] = message.text
    msg = bot.send_message(message.chat.id, "⏳ Укажите длительность занятия (в минутах):")
    bot.register_next_step_handler(msg, process_quest_duration, quest_data)

def process_quest_duration(message, quest_data):
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError
        quest_data["duration"] = duration
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Ошибка: введите положительное число для длительности занятия. Попробуйте ещё раз:")
        bot.register_next_step_handler(msg, process_quest_duration, quest_data)
        return
    
    msg = bot.send_message(message.chat.id, "💰 Укажите цену за участие (руб.):")
    bot.register_next_step_handler(msg, process_quest_price, quest_data)

def process_quest_price(message, quest_data):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
        quest_data["price"] = price
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Ошибка: введите корректное число для цены. Попробуйте ещё раз:")
        bot.register_next_step_handler(msg, process_quest_price, quest_data)
        return
    
    msg = bot.send_message(
        message.chat.id,
        "👥 Укажите минимальное и максимальное количество игроков (через пробел, например: 2 5):"
    )
    bot.register_next_step_handler(msg, process_quest_players, quest_data)

def process_quest_players(message, quest_data):
    try:
        min_players, max_players = map(int, message.text.split())
        if min_players <= 0 or max_players <= 0 or min_players > max_players:
            raise ValueError
        quest_data["min_players"] = min_players
        quest_data["max_players"] = max_players
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ Ошибка: введите два числа через пробел (мин макс), где мин <= макс. Попробуйте ещё раз:"
        )
        bot.register_next_step_handler(msg, process_quest_players, quest_data)
        return
    
    msg = bot.send_message(
        message.chat.id,
        "⚡ Выберите сложность кружка:\n1. Начинающий\n2. Средний\n3. Продвинутый"
    )
    bot.register_next_step_handler(msg, process_quest_difficulty, quest_data)

def process_quest_difficulty(message, quest_data):
    difficulty_map = {
        "1": "Легкая",
        "2": "Средняя",
        "3": "Сложная"
    }
    
    if message.text not in difficulty_map:
        msg = bot.send_message(
            message.chat.id,
            "❌ Ошибка: выберите число от 1 до 3. Попробуйте ещё раз:"
        )
        bot.register_next_step_handler(msg, process_quest_difficulty, quest_data)
        return
    
    quest_data["difficulty"] = difficulty_map[message.text]
    
    # Собираем все данные
    try:
        query = """
            INSERT INTO circles (
                name, description, duration, price, 
                min_players, max_players, difficulty
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            quest_data["name"],
            quest_data["description"],
            quest_data["duration"],
            quest_data["price"],
            quest_data["min_players"],
            quest_data["max_players"],
            quest_data["difficulty"]
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        bot.send_message(message.chat.id, "✅ Кружок успешно добавлен!")
        show_admin_panel(message.chat.id, message.message_id)
        
    except Exception as e:
        logging.error(f"Ошибка при добавлении кружка: {str(e)}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при добавлении кружка.")

def admin_manage_quests(message):
    try:
        query = "SELECT id, name FROM circles ORDER BY id DESC"
        cursor.execute(query)
        quests = cursor.fetchall()

        markup = types.InlineKeyboardMarkup()

        if not quests:
            markup.add(types.InlineKeyboardButton("➕ Добавить кружок", callback_data="admin_add_quest"))
            markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu"))
            try:
                bot.edit_message_text(
                    "ℹ️ Нет доступных кружков. Хотите добавить новый?",
                    message.chat.id,
                    message.message_id,
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    message.chat.id,
                    "ℹ️ Нет доступных кружков. Хотите добавить новый?",
                    reply_markup=markup
                )
            return

        text = "⚙ Управление квестами:\nВыберите квест для редактирования:"
        for quest in quests:
            quest_id, name = quest
            btn = types.InlineKeyboardButton(
                f"{name} (ID:{quest_id})", 
                callback_data=f"admin_quest_{quest_id}"
            )
            markup.add(btn)

        markup.add(types.InlineKeyboardButton("➕ Добавить квест", callback_data="admin_add_quest"))
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu"))

        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )

    except Exception as e:
        logging.error(f"Ошибка в admin_manage_quests: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, "⚠️ Ошибка при загрузке квестов")

def admin_show_quest_details(message, quest_id):
    try:
        if not str(quest_id).isdigit():
            raise ValueError("Неверный ID квеста")

        query = """
            SELECT id, name, description, duration, 
                   min_players, max_players, price, difficulty
            FROM circles 
            WHERE id = %s
        """
        cursor.execute(query, (quest_id,))
        quest = cursor.fetchone()

        if not quest:
            bot.send_message(message.chat.id, "⚠️ Кружок не найден")
            return

        text = (
            f"🔍 *Детали кружка ID: {quest[0]}*\n\n"
            f"📌 *Название:* {quest[1]}\n"
            f"📝 *Описание:* {quest[2]}\n"
            f"⏱ *Длительность:* {quest[3]} мин\n"
            f"💰 *Цена:* {quest[6]} руб\n"
            f"👥 *Участники:* от {quest[4]} до {quest[5]}\n"
            f"⚡ *Сложность:* {quest[7]}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_edit = types.InlineKeyboardButton("✏️ Редактировать", callback_data=f"admin_edit_menu_{quest_id}")
        btn_delete = types.InlineKeyboardButton("❌ Удалить", callback_data=f"admin_confirm_delete_{quest_id}")
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_manage_quests")
        
        markup.add(btn_edit, btn_delete)
        markup.add(btn_back)

        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                text,
                parse_mode="Markdown",
                reply_markup=markup
            )

    except Exception as e:
        logging.error(f"Ошибка в admin_show_quest_details: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, f"⚠️ Ошибка при загрузке квеста: {str(e)}")

def admin_edit_menu(message, quest_id):
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        fields = [
            ("Название", "name"),
            ("Описание", "description"),
            ("Длительность", "duration"),
            ("Цена", "price"),
            ("Мин. игроки", "min_players"),
            ("Макс. игроки", "max_players"),
            ("Сложность", "difficulty")
        ]
        
        for field_name, field_key in fields:
            btn = types.InlineKeyboardButton(
                f"✏️ {field_name}", 
                callback_data=f"admin_edit_{field_key}_{quest_id}"
            )
            markup.add(btn)
        
        btn_back = types.InlineKeyboardButton(
            "⬅ Назад", 
            callback_data=f"admin_quest_{quest_id}"
        )
        markup.add(btn_back)
        
        try:
            bot.edit_message_text(
                "✏️ Выберите поле для редактирования:",
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                "✏️ Выберите поле для редактирования:",
                reply_markup=markup
            )
    
    except Exception as e:
        logging.error(f"Ошибка в admin_edit_menu: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, "⚠️ Ошибка при открытии меню редактирования")

def admin_edit_field(message, quest_id, field_name):
    try:
        query = f"SELECT {field_name} FROM circles WHERE id = %s"
        cursor.execute(query, (quest_id,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("Квест не найден")
            
        current_value = result[0]
        
        msg = bot.send_message(
            message.chat.id,
            f"✍ Текущее значение '{field_name}': {current_value}\n"
            f"Введите новое значение:"
        )
        bot.register_next_step_handler(
            msg, 
            lambda m: process_field_update(m, quest_id, field_name)
        )
        
    except Exception as e:
        logging.error(f"Ошибка в admin_edit_field: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, f"⚠️ Ошибка при редактировании поля: {str(e)}")

def process_field_update(message, quest_id, field_name):
    try:
        new_value = message.text
        
        # Преобразование типов для числовых полей
        if field_name in ['duration', 'min_players', 'max_players']:
            try:
                new_value = int(new_value)
            except ValueError:
                bot.send_message(
                    message.chat.id, 
                    f"❌ Ошибка: введите целое число для поля '{field_name}'"
                )
                return
                
        elif field_name == 'price':
            try:
                new_value = float(new_value)
            except ValueError:
                bot.send_message(
                    message.chat.id, 
                    "❌ Ошибка: введите число для цены (например: 2500.00)"
                )
                return
        # Валидация для поля difficulty
        if field_name == 'difficulty':
            allowed_values = ['Легкая', 'Средняя', 'Сложная']
            if new_value not in allowed_values:
                bot.send_message(
                    message.chat.id, 
                    "❌ Недопустимое значение сложности. Допустимые значения: Легкая, Средняя, Сложная"
                )
                return
        
        # Безопасное обновление поля
        safe_fields = ['name', 'description', 'duration', 'price', 
                      'min_players', 'max_players', 'difficulty']
        
        if field_name not in safe_fields:
            raise ValueError("Недопустимое имя поля")
        
        query = f"UPDATE quests SET {field_name} = %s WHERE id = %s"
        cursor.execute(query, (new_value, quest_id))
        conn.commit()
        
        bot.send_message(message.chat.id, f"✅ Поле '{field_name}' успешно обновлено!")
        admin_show_quest_details(message, quest_id)
        
    except Exception as e:
        logging.error(f"Ошибка при обновлении поля: {str(e)}")
        bot.send_message(message.chat.id, f"❌ Ошибка при обновлении: {str(e)}")
def admin_confirm_delete(message, quest_id):
    try:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_yes = types.InlineKeyboardButton(
            "✅ Да, удалить", 
            callback_data=f"admin_delete_{quest_id}"
        )
        btn_no = types.InlineKeyboardButton(
            "❌ Нет, отмена", 
            callback_data=f"admin_quest_{quest_id}"
        )
        markup.add(btn_yes, btn_no)
        
        try:
            bot.edit_message_text(
                "⚠️ Вы уверены, что хотите удалить этот квест?\n"
                "Это действие нельзя отменить!",
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                "⚠️ Вы уверены, что хотите удалить этот квест?\n"
                "Это действие нельзя отменить!",
                reply_markup=markup
            )
    
    except Exception as e:
        logging.error(f"Ошибка в admin_confirm_delete: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, "⚠️ Ошибка при подтверждении удаления")

def admin_delete_quest(message, quest_id):
    try:
        # Проверка существования квеста
        cursor.execute("SELECT name FROM circles WHERE id = %s", (quest_id,))
        result = cursor.fetchone()
        if not result:
            bot.send_message(message.chat.id, "❌ Квест не найден")
            return

        quest_name = result[0]
        
        # Удаление связанных записей
        cursor.execute("DELETE FROM bookings WHERE quest_id = %s", (quest_id,))
        cursor.execute("DELETE FROM promotions WHERE quest_id = %s", (quest_id,))
        cursor.execute("DELETE FROM reviews WHERE quest_id = %s", (quest_id,))
        
        # Удаление квеста
        cursor.execute("DELETE FROM circles WHERE id = %s", (quest_id,))
        conn.commit()
        
        bot.send_message(message.chat.id, f"✅ Квест '{quest_name}' успешно удален")
        time.sleep(1)
        admin_manage_quests(message)
        
    except Exception as e:
        logging.error(f"Ошибка при удалении квеста: {str(e)}")
        bot.send_message(message.chat.id, f"❌ Ошибка при удалении квеста: {str(e)}")

def admin_manage_promos(message):
    try:
        query = "SELECT id, title, valid_until FROM promotions ORDER BY valid_until DESC"
        cursor.execute(query)
        promos = cursor.fetchall()

        text = "🎁 Управление акциями:\n\n"
        markup = types.InlineKeyboardMarkup()

        if not promos:
            text += "Акций пока нет."
            btn_add = types.InlineKeyboardButton("➕ Добавить акцию", callback_data="admin_create_promo")
            btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
            markup.add(btn_add, btn_back)
        else:
            for promo in promos:
                promo_id, title, valid_until = promo
                text += f"• {title} (до {valid_until})\n"
                btn = types.InlineKeyboardButton(f"🔍 {title}", callback_data=f"admin_promo_{promo_id}")
                markup.add(btn)
            
            btn_add = types.InlineKeyboardButton("➕ Добавить акцию", callback_data="admin_create_promo")
            btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
            markup.add(btn_add, btn_back)

        try:
            bot.edit_message_text(
                text,
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup
            )

    except Exception as e:
        logging.error(f"Ошибка в admin_manage_promos: {str(e)}", exc_info=True)
        bot.send_message(message.chat.id, "⚠️ Ошибка при загрузке акций")

def admin_promo_detail(message, promo_id):
    query = "SELECT title, description, discount, quest_id, valid_until FROM promotions WHERE id=%s"
    cursor.execute(query, (promo_id,))
    promo = cursor.fetchone()
    
    if not promo:
        bot.send_message(message.chat.id, "⚠️ Акция не найдена")
        return
        
    title, description, discount, quest_id, valid_until = promo
    text = (
        f"🔍 *Детали акции ID: {promo_id}*\n\n"
        f"📌 *Название:* {title}\n"
        f"📝 *Описание:* {description}\n"
        f"💸 *Скидка:* {discount} руб\n"
        f"🎮 *ID квеста:* {quest_id if quest_id else 'Для всех'}\n"
        f"📅 *Действует до:* {valid_until}"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_edit = types.InlineKeyboardButton("✏️ Редактировать", callback_data=f"admin_edit_promo_{promo_id}")
    btn_delete = types.InlineKeyboardButton("❌ Удалить", callback_data=f"admin_confirm_delete_promo_{promo_id}")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_manage_promos")
    
    markup.add(btn_edit, btn_delete, btn_back)

    try:
        bot.edit_message_text(
            text,
            message.chat.id,
            message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

def admin_create_promo_start(message):
    msg = bot.send_message(message.chat.id, "✍ Введите название акции:")
    bot.register_next_step_handler(msg, process_promo_title)

def process_promo_title(message):
    promo_data = {"title": message.text}
    msg = bot.send_message(message.chat.id, "📝 Введите описание акции:")
    bot.register_next_step_handler(msg, process_promo_description, promo_data)

def process_promo_description(message, promo_data):
    promo_data["description"] = message.text
    msg = bot.send_message(message.chat.id, "💸 Введите размер скидки (руб.):")
    bot.register_next_step_handler(msg, process_promo_discount, promo_data)

def process_promo_discount(message, promo_data):
    try:
        discount = float(message.text)
        if discount <= 0:
            raise ValueError
        promo_data["discount"] = discount
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Ошибка: введите положительное число для скидки. Попробуйте ещё раз:")
        bot.register_next_step_handler(msg, process_promo_discount, promo_data)
        return
    
    msg = bot.send_message(message.chat.id, "🔢 Укажите ID квеста (или 'all' для всех квестов):")
    bot.register_next_step_handler(msg, process_promo_quest, promo_data)

def process_promo_quest(message, promo_data):
    quest_id = None if message.text.lower() == "all" else message.text
    promo_data["quest_id"] = quest_id
    
    msg = bot.send_message(message.chat.id, "📅 Укажите дату окончания акции (ГГГГ-ММ-ДД):")
    bot.register_next_step_handler(msg, process_promo_date, promo_data)

def process_promo_date(message, promo_data):
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        if end_date < datetime.today().date():
            raise ValueError
        promo_data["end_date"] = end_date
    except:
        msg = bot.send_message(
            message.chat.id,
            "❌ Ошибка: введите дату в формате ГГГГ-ММ-ДД (будущая дата). Попробуйте ещё раз:"
        )
        bot.register_next_step_handler(msg, process_promo_date, promo_data)
        return
    
    try:
        query = """
            INSERT INTO promotions (
                title, description, discount, quest_id, valid_until
            ) VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            promo_data["title"],
            promo_data["description"],
            promo_data["discount"],
            promo_data["quest_id"],
            promo_data["end_date"]
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        bot.send_message(message.chat.id, "✅ Акция успешно создана!")
        show_admin_panel(message.chat.id, message.message_id)
        
    except Exception as e:
        logging.error(f"Ошибка при создании акции: {str(e)}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при создании акции.")

def admin_notify_choose_employee(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_all = types.InlineKeyboardButton("👥 Всем сотрудникам", callback_data="admin_notify_all")
    markup.add(btn_all)
    
    for emp_id in EMPLOYEES:
        # Получаем имя сотрудника из базы
        cursor.execute("SELECT first_name FROM users WHERE id=%s", (emp_id,))
        result = cursor.fetchone()
        name = result[0] if result else f"Сотрудник {emp_id}"
        
        btn = types.InlineKeyboardButton(f"👤 {name}", callback_data=f"admin_notify_{emp_id}")
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            "👥 Выберите сотрудников для оповещения:",
            message.chat.id,
            message.message_id,
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            "👥 Выберите сотрудников для оповещения:",
            reply_markup=markup
        )

def admin_send_notification(call, employee_id):
    if employee_id == "all":
        employee_ids = EMPLOYEES
    else:
        employee_ids = [int(employee_id)]
    
    msg = bot.send_message(
        call.message.chat.id,
        "📢 Введите сообщение для оповещения:"
    )
    bot.register_next_step_handler(msg, lambda m: admin_process_notification(m, employee_ids))

def admin_process_notification(message, employee_ids):
    notify_text = message.text
    success_count = 0
    
    for emp_id in employee_ids:
        try:
            bot.send_message(emp_id, f"📢 *Оповещение от администратора:*\n\n{notify_text}", parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            logging.error(f"Ошибка при отправке сотруднику {emp_id}: {e}")
    
    bot.send_message(
        message.chat.id,
        f"✅ Оповещение отправлено {success_count}/{len(employee_ids)} сотрудникам!"
    )

def admin_list_bookings(message):
    query = """
        SELECT b.id, q.name, b.date, b.time, b.status 
        FROM bookings b 
        JOIN quests q ON b.quest_id = q.id 
        WHERE status IN ('pending', 'confirmed')
        ORDER BY b.date ASC
    """
    cursor.execute(query)
    bookings = cursor.fetchall()
    
    # Статусы на русском
    status_translation = {
        'pending': 'ожидает подтверждения',
        'confirmed': 'подтверждена',
        'cancelled': 'отменена',
        'completed': 'завершена'
    }
    
    if not bookings:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
        markup.add(btn_back)
        
        try:
            bot.edit_message_text(
                "ℹ️ Нет активных бронирований.",
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                "ℹ️ Нет активных бронирований.",
                reply_markup=markup
            )
        return
    
    text = "🔔 *Активные бронирования:*\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for booking in bookings:
        booking_id, quest_name, date, time_slot, status = booking
        status_text = status_translation.get(status, status)
        
        text += (
            f"📌 *Бронь №{booking_id}: {quest_name}*\n"
            f"📅 {date} | ⏰ {time_slot}\n"
            f"🔄 Статус: {status_text}\n\n"
        )
        
        btn = types.InlineKeyboardButton(
            f"Бронь №{booking_id}", 
            callback_data=f"admin_booking_{booking_id}"
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def admin_booking_detail(message, booking_id):
    query = """
        SELECT 
            b.id, q.name, b.date, b.time, 
            b.players, b.prepayment, b.status,
            u.first_name, u.username, u.id as user_id
        FROM bookings b 
        JOIN quests q ON b.quest_id = q.id 
        JOIN users u ON b.user_id = u.id
        WHERE b.id = %s
    """
    cursor.execute(query, (booking_id,))
    booking = cursor.fetchone()
    
    if not booking:
        try:
            bot.edit_message_text("❌ Бронь не найдена.", message.chat.id, message.message_id)
        except:
            bot.send_message(message.chat.id, "❌ Бронь не найдена.")
        return
    
    # Статусы на русском
    status_translation = {
        'pending': 'ожидает подтверждения',
        'confirmed': 'подтверждена',
        'cancelled': 'отменена',
        'completed': 'завершена'
    }
    status_text = status_translation.get(booking[6], booking[6])
    
    text = (
        f"📝 *Детали брони №{booking[0]}*\n\n"
        f"🎮 *Квест:* **{booking[1]}**\n"
        f"👤 *Клиент:* **{booking[7]}** (@{booking[8] if booking[8] else 'без username'})\n"
        f"🆔 *ID клиента:* {booking[9]}\n"
        f"📞 *Связаться:* [Написать](tg://user?id={booking[9]})\n"
        f"📅 *Дата:* **{booking[2]}**\n"
        f"⏰ *Время:* **{booking[3]}**\n"
        f"👥 *Участник:* **1**\n"
        f"💳 *Предоплата:* **{'✅ Да' if booking[5] else '❌ Нет'}**\n"
        f"🔄 *Статус брони:* **{status_text}**"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if booking[6] == 'pending':
        btn_confirm = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{booking[0]}")
        btn_cancel = types.InlineKeyboardButton("❌ Отменить", callback_data=f"admin_cancel_{booking[0]}")
        markup.row(btn_confirm, btn_cancel)
    elif booking[6] == 'confirmed':
        btn_cancel = types.InlineKeyboardButton("❌ Отменить", callback_data=f"admin_cancel_{booking[0]}")
        markup.add(btn_cancel)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_bookings")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id, 
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )

def admin_confirm_booking(message, booking_id):
    query = "UPDATE bookings SET status='confirmed' WHERE id=%s"
    try:
        cursor.execute(query, (booking_id,))
        conn.commit()
        
        # Получаем информацию о брони для уведомления пользователя
        query = """
            SELECT b.user_id, q.name, b.date, b.time 
            FROM bookings b
            JOIN quests q ON b.quest_id = q.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        
        if result:
            user_id, quest_name, date, time_slot = result
            bot.send_message(
                user_id,
                f"🎉 Ваша бронь на квест *{quest_name}* подтверждена!\n\n"
                f"📅 Дата: *{date}*\n"
                f"⏰ Время: *{time_slot}*\n\n"
                f"Ждем вас в указанное время!",
                parse_mode="Markdown"
            )
        
        try:
            bot.edit_message_text(
                f"✅ Бронь №{booking_id} подтверждена.",
                message.chat.id, 
                message.message_id, 
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                message.chat.id,
                f"✅ Бронь №{booking_id} подтверждена.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Ошибка при подтверждении брони: {str(e)}")
        try:
            bot.edit_message_text(
                f"❌ Ошибка при подтверждении брони: {str(e)}",
                message.chat.id,
                message.message_id
            )
        except:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка при подтверждении брони: {str(e)}"
            )

def admin_cancel_booking(message, booking_id):
    query = "UPDATE bookings SET status='cancelled' WHERE id=%s"
    try:
        cursor.execute(query, (booking_id,))
        conn.commit()
        
        # Получаем информацию о брони для уведомления пользователя
        query = """
            SELECT b.user_id, q.name, b.date, b.time 
            FROM bookings b
            JOIN quests q ON b.quest_id = q.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        
        if result:
            user_id, quest_name, date, time_slot = result
            bot.send_message(
                user_id,
                f"😔 Ваша бронь на квест *{quest_name}* отменена администратором.\n\n"
                f"📅 Дата: *{date}*\n"
                f"⏰ Время: *{time_slot}*\n\n"
                f"По всем вопросам обращайтесь в поддержку.",
                parse_mode="Markdown"
            )
        
        try:
            bot.edit_message_text(
                f"✅ Бронь №{booking_id} отменена.",
                message.chat.id, 
                message.message_id, 
                parse_mode="Markdown"
            )
        except:
            bot.send_message(
                message.chat.id,
                f"✅ Бронь №{booking_id} отменена.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Ошибка при отмене брони: {str(e)}")
        try:
            bot.edit_message_text(
                f"❌ Ошибка при отмене брони: {str(e)}",
                message.chat.id,
                message.message_id
            )
        except:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка при отмене брони: {str(e)}"
            )

def admin_list_support_messages(message):
    query = "SELECT id, user_id, message, created_at FROM support_messages WHERE response IS NULL ORDER BY created_at DESC"
    cursor.execute(query)
    support_msgs = cursor.fetchall()
    
    if not support_msgs:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
        markup.add(btn_back)
        
        try:
            bot.edit_message_text(
                "ℹ️ Новых вопросов нет.",
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                "ℹ️ Новых вопросов нет.",
                reply_markup=markup
            )
        return
    
    text = "📬 *Новые вопросы от пользователей:*\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for msg_row in support_msgs:
        support_id, user_id, message_text, created_at = msg_row
        snippet = message_text[:30] + "..." if len(message_text) > 30 else message_text
        btn = types.InlineKeyboardButton(f"ID {support_id}: {snippet}", callback_data=f"admin_support_{support_id}")
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id, 
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def admin_support_detail(message, support_id):
    query = """
        SELECT 
            s.id, s.user_id, s.message, s.created_at,
            u.first_name, u.username
        FROM support_messages s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """
    cursor.execute(query, (support_id,))
    support_msg = cursor.fetchone()
    
    if not support_msg:
        try:
            bot.edit_message_text("❌ Сообщение не найдено.", message.chat.id, message.message_id)
        except:
            bot.send_message(message.chat.id, "❌ Сообщение не найдено.")
        return
    
    text = (
        f"📬 *Сообщение ID {support_msg[0]}*\n\n"
        f"👤 *От пользователя:* {support_msg[4]} (@{support_msg[5] if support_msg[5] else 'без username'})\n"
        f"🆔 *ID пользователя:* {support_msg[1]}\n"
        f"📞 *Связаться:* [Написать](tg://user?id={support_msg[1]})\n"
        f"⏰ *Отправлено:* {support_msg[3]}\n\n"
        f"💬 *Вопрос:*\n{support_msg[2]}"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_answer = types.InlineKeyboardButton("✍ Ответить", callback_data=f"admin_answer_{support_msg[0]}")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_support")
    
    markup.add(btn_answer, btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )

def admin_process_answer(message, support_id):
    answer = message.text
    
    # Получаем информацию о вопросе
    query = "SELECT user_id, message FROM support_messages WHERE id = %s"
    cursor.execute(query, (support_id,))
    support_info = cursor.fetchone()
    
    if not support_info:
        bot.send_message(message.chat.id, "❌ Вопрос не найден.")
        return
    
    user_id, question_text = support_info
    
    try:
        # Отправляем ответ пользователю
        bot.send_message(
            user_id, 
            f"📩 *Ответ администратора на ваш вопрос:*\n\n"
            f"*Ваш вопрос:*\n{question_text}\n\n"
            f"*Ответ администратора:*\n{answer}",
            parse_mode="Markdown"
        )
        
        # Помечаем вопрос как отвеченный
        query = "UPDATE support_messages SET response = %s, answered_at = NOW() WHERE id = %s"
        cursor.execute(query, (answer, support_id))
        conn.commit()
        
        bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа: {str(e)}")
        bot.send_message(message.chat.id, "❌ Не удалось отправить ответ пользователю.")

def admin_manage_reviews(message):
    query = """
        SELECT r.id, r.review, r.created_at, u.first_name, u.username 
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        ORDER BY r.created_at DESC
        LIMIT 20
    """
    cursor.execute(query)
    reviews = cursor.fetchall()
    
    if not reviews:
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
        markup.add(btn_back)
        
        try:
            bot.edit_message_text(
                "ℹ️ Отзывов пока нет.",
                message.chat.id,
                message.message_id,
                reply_markup=markup
            )
        except:
            bot.send_message(
                message.chat.id,
                "ℹ️ Отзывов пока нет.",
                reply_markup=markup
            )
        return
    
    text = "⭐ *Последние отзывы:*\n\n"
    markup = types.InlineKeyboardMarkup()
    
    for review in reviews:
        review_id, review_text, created_at, first_name, username = review
        snippet = review_text[:30] + "..." if len(review_text) > 30 else review_text
        text += f"👤 *{first_name}*: {snippet}\n\n"
        
        btn = types.InlineKeyboardButton(
            f"Отзыв №{review_id}", 
            callback_data=f"admin_review_{review_id}"
        )
        markup.add(btn)
    
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_menu")
    markup.add(btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup
        )

def admin_review_detail(message, review_id):
    query = """
        SELECT 
            r.id, r.review, r.created_at, 
            u.first_name, u.username, u.id as user_id
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = %s
    """
    cursor.execute(query, (review_id,))
    review = cursor.fetchone()
    
    if not review:
        try:
            bot.edit_message_text("❌ Отзыв не найден.", message.chat.id, message.message_id)
        except:
            bot.send_message(message.chat.id, "❌ Отзыв не найден.")
        return
    
    text = (
        f"⭐ *Детали отзыва №{review[0]}*\n\n"
        f"👤 *Автор:* {review[3]} (@{review[4] if review[4] else 'без username'})\n"
        f"🆔 *ID автора:* {review[5]}\n"
        f"📞 *Связаться:* [Написать](tg://user?id={review[5]})\n"
        f"⏰ *Дата:* {review[2]}\n\n"
        f"💬 *Отзыв:*\n{review[1]}"
    )
    
    markup = types.InlineKeyboardMarkup()
    btn_answer = types.InlineKeyboardButton("✍ Ответить", callback_data=f"admin_answer_review_{review[0]}")
    btn_delete = types.InlineKeyboardButton("❌ Удалить", callback_data=f"admin_delete_review_{review[0]}")
    btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data="admin_reviews")
    
    markup.add(btn_answer, btn_delete, btn_back)
    
    try:
        bot.edit_message_text(
            text, 
            message.chat.id, 
            message.message_id,
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except:
        bot.send_message(
            message.chat.id,
            text, 
            parse_mode="Markdown", 
            reply_markup=markup,
            disable_web_page_preview=True
        )

def admin_answer_review(message, review_id):
    msg = bot.send_message(
        message.chat.id,
        "✍ Введите ответ на отзыв:"
    )
    bot.register_next_step_handler(msg, lambda m: admin_process_review_answer(m, review_id))

def admin_process_review_answer(message, review_id):
    answer = message.text
    
    # Получаем информацию об отзыве
    query = """
        SELECT r.user_id, r.review, u.first_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.id = %s
    """
    cursor.execute(query, (review_id,))
    review_info = cursor.fetchone()
    
    if not review_info:
        bot.send_message(message.chat.id, "❌ Отзыв не найден.")
        return
    
    user_id, review_text, first_name = review_info
    
    try:
        # Отправляем ответ пользователю
        bot.send_message(
            user_id,
            f"📩 *Ответ администратора на ваш отзыв:*\n\n"
            f"*Ваш отзыв:*\n{review_text}\n\n"
            f"*Ответ администратора:*\n{answer}",
            parse_mode="Markdown"
        )
        
        # Помечаем отзыв как отвеченный
        query = "UPDATE reviews SET admin_response = %s WHERE id = %s"
        cursor.execute(query, (answer, review_id))
        conn.commit()
        
        bot.send_message(message.chat.id, "✅ Ответ отправлен пользователю!")
        
    except Exception as e:
        logging.error(f"Ошибка при отправке ответа: {str(e)}")
        bot.send_message(message.chat.id, "❌ Не удалось отправить ответ пользователю.")

def admin_delete_review(message, review_id):
    try:
        query = "DELETE FROM reviews WHERE id = %s"
        cursor.execute(query, (review_id,))
        conn.commit()
        
        bot.send_message(message.chat.id, f"✅ Отзыв №{review_id} удален!")
        time.sleep(1)
        admin_manage_reviews(message)
        
    except Exception as e:
        logging.error(f"Ошибка при удалении отзыва: {str(e)}")
        bot.send_message(message.chat.id, "❌ Не удалось удалить отзыв.")

# ====================== ОБЪЕДИНЁННЫЙ CALLBACK-ОБРАБОТЧИК ======================

@bot.callback_query_handler(func=lambda call: True)
def unified_callback_handler(call):
    data = call.data
    
    # Проверка доступа к админ-панели
    if data.startswith("admin_") and call.message.chat.id not in EMPLOYEES:
        bot.answer_callback_query(call.id, "⛔ У вас нет доступа к админ-панели.")
        return
        
    # Обработка админских команд
    if data.startswith("admin_"):
        handle_admin_callback(call)
    else:
        handle_client_callback(call)

def handle_admin_callback(call):
    if call.data == "admin_menu":
        show_admin_panel(call.message.chat.id, call.message.message_id)
            
    elif call.data == "admin_add_quest":
        add_quest_start(call.message)
            
    elif call.data == "admin_manage_quests":
        admin_manage_quests(call.message)
            
    elif call.data.startswith("admin_quest_"):
        quest_id = call.data.split('_')[2]
        admin_show_quest_details(call.message, quest_id)
            
    elif call.data.startswith("admin_edit_menu_"):
        quest_id = call.data.split('_')[3]
        admin_edit_menu(call.message, quest_id)
            
    elif call.data.startswith("admin_edit_") and not call.data.startswith("admin_edit_menu_"):
        parts = call.data.split('_')
        field_name = parts[2]
        quest_id = parts[3]
        admin_edit_field(call.message, quest_id, field_name)
            
    elif call.data.startswith("admin_confirm_delete_"):
        quest_id = call.data.split('_')[3]
        admin_confirm_delete(call.message, quest_id)
            
    elif call.data.startswith("admin_delete_") and not call.data.startswith("admin_delete_confirm_"):
        quest_id = call.data.split('_')[2]
        admin_delete_quest(call.message, quest_id)
            
    elif call.data == "admin_manage_promos":
        admin_manage_promos(call.message)
            
    elif call.data.startswith("admin_promo_"):
        promo_id = call.data.split('_')[2]
        admin_promo_detail(call.message, promo_id)
            
    elif call.data == "admin_create_promo":
        admin_create_promo_start(call.message)
            
    elif call.data == "admin_notify":
        admin_notify_choose_employee(call.message)
            
    elif call.data.startswith("admin_notify_"):
        if call.data == "admin_notify_all":
            admin_send_notification(call, "all")
        else:
            employee_id = call.data.split('_')[2]
            admin_send_notification(call, employee_id)
            
    elif call.data == "admin_bookings":
        admin_list_bookings(call.message)
            
    elif call.data.startswith("admin_booking_"):
        booking_id = call.data.split('_')[2]
        admin_booking_detail(call.message, booking_id)
            
    elif call.data.startswith("admin_confirm_"):
        booking_id = call.data.split('_')[2]
        admin_confirm_booking(call.message, booking_id)
            
    elif call.data.startswith("admin_cancel_"):
        booking_id = call.data.split('_')[2]
        admin_cancel_booking(call.message, booking_id)
            
    elif call.data == "admin_support":
        admin_list_support_messages(call.message)
            
    elif call.data.startswith("admin_support_"):
        support_id = call.data.split('_')[2]
        admin_support_detail(call.message, support_id)
            
    elif call.data.startswith("admin_answer_"):
        support_id = call.data.split('_')[2]
        msg = bot.send_message(call.message.chat.id, "✍ Введите ответ пользователю:")
        bot.register_next_step_handler(msg, lambda m: admin_process_answer(m, support_id))
            
    elif call.data == "admin_reviews":
        admin_manage_reviews(call.message)
        
    elif call.data.startswith("admin_review_"):
        review_id = call.data.split('_')[2]
        admin_review_detail(call.message, review_id)
        
    elif call.data.startswith("admin_answer_review_"):
        review_id = call.data.split('_')[3]
        admin_answer_review(call.message, review_id)
        
    elif call.data.startswith("admin_delete_review_"):
        review_id = call.data.split('_')[3]
        admin_delete_review(call.message, review_id)
  
def handle_client_callback(call):
    data = call.data

    # Основная навигация
    if data == "back_main":
        send_main_menu(call.message.chat.id, call.message.message_id)
    elif data == "catalog":
        show_catalog(call.message, call.message.message_id)
    elif data == "support":
        support_menu(call.message, call.message.message_id)
    elif data == "my_bookings":
        show_bookings(call.message, call.message.message_id)
    elif data == "bookings_upcoming":
        show_upcoming_bookings(call.message, call.message.message_id)
    elif data == "bookings_past":
        show_past_bookings(call.message, call.message.message_id)
    elif data == "promotions":
        show_promotions(call.message, call.message.message_id)
    elif data == "recommendations":
        show_recommendations(call.message, call.message.message_id)
    elif data.startswith("recommend_"):
        quest_id = data.split("_")[1]
        show_recommendations_for_quest(call.message, quest_id, call.message.message_id)
    elif data == "genres":
        show_genres(call.message, call.message.message_id)
    elif data == "all_circles":
        show_quest_list(call.message, message_id=call.message.message_id)
    elif data.startswith("quests_adults_"):
        genre = data.split("_")[2]
        show_quest_list(call.message, genre=genre, message_id=call.message.message_id)
    elif data in ["танцы", "рисование", "пилатес", "йога", "спорт"]:
        show_quest_list(call.message, genre=data, message_id=call.message.message_id)
    elif data == "back_catalog":
        show_catalog(call.message, call.message.message_id)
    
    # Выбор квеста и информация о квесте
    elif data.startswith("quest_"):
        quest_id = data.split("_")[1]
        show_quest_info(call.message, quest_id, call.message.message_id)
    elif data.startswith("book_quest_"):
        quest_id = data.split("_")[2]
        prompt_date_selection(call.message, quest_id, message_id=call.message.message_id)
    elif data.startswith("bookpromo_"):
        parts = data.split("_")
        quest_id = parts[1]
        promo_id = parts[2]
        prompt_date_selection(call.message, quest_id, promo_id, message_id=call.message.message_id)
    elif data.startswith("calendar_"):
        parts = data.split("_")
        quest_id = parts[1]
        year = int(parts[2])
        month = int(parts[3])
        promo_id = parts[4] if len(parts) > 4 and parts[4] != '' else None
        prompt_date_selection(call.message, quest_id, promo_id, call.message.message_id, year, month)
    elif data.startswith("back_date_"):
        quest_id = data.split("_")[2]
        show_quest_info(call.message, quest_id, call.message.message_id)
    elif data.startswith("date_"):
        parts = data.split("_")
        quest_id, selected_date = parts[1], parts[2]
        promo_id = parts[3] if len(parts) > 3 else None
        prompt_time_selection(call.message, quest_id, selected_date, promo_id, message_id=call.message.message_id)
    elif data.startswith("back_time_"):
        parts = data.split("_")
        quest_id, selected_date = parts[2], parts[3]
        promo_id = parts[4] if len(parts) > 4 else None
        prompt_date_selection(call.message, quest_id, promo_id, message_id=call.message.message_id)
    elif data.startswith("time_"):
        parts = data.split("_")
        quest_id, selected_date, selected_time = parts[1], parts[2], parts[3]
        promo_id = parts[4] if len(parts) > 4 else None
        confirm_booking_details(call.message, quest_id, selected_date, selected_time, 1, promo_id, message_id=call.message.message_id)
    elif data.startswith("confirm|"):
        parts = data.split('|')
        if len(parts) < 6:
            logging.error(f"Некорректный callback_data: {data}")
            bot.answer_callback_query(call.id, "Произошла ошибка. Пожалуйста, начните заново.")
            return
        quest_id = parts[1]
        selected_date = parts[2]
        selected_time = parts[3]
        players = parts[4]
        prepayment_flag = parts[5]
        promo_id = parts[6] if len(parts) > 6 and parts[6] != '' else None
        complete_booking(call, quest_id, selected_date, selected_time, players, prepayment_flag, promo_id)
    
    # Раздел "Поддержка"
    elif data == "support_menu":
        support_menu(call.message)
    elif data == "support_about":
        support_about(call.message, call.message.message_id)
    elif data == "support_contacts":
        support_contacts(call.message, call.message.message_id)
    elif data == "support_faq":
        support_faq(call.message)
    elif data == "support_ask":
        support_ask(call.message)
    elif data == "support_reviews":
        support_reviews(call.message)
    elif data == "support_add_review":
        support_add_review(call.message)
    elif data == "support_tips":
        support_tips(call.message)
    elif data == "support_rules":
        support_rules(call.message)
    elif data == "support_bonus":
        support_bonus(call.message)
    elif data == "support_subscribe":
        handle_support_subscribe(call)
    
    # Раздел "Мои брони"
    elif data.startswith("view_booking_"):
        booking_id = data.split("_")[2]
        show_booking_detail(call.message, booking_id, call.message.message_id)
    elif data.startswith("cancel_booking_"):
        booking_id = data.split("_")[2]
        process_cancel_booking(call.message, booking_id)
    elif data.startswith("confirm_cancel_"):
        booking_id = data.split("_")[2]
        finalize_cancel_booking(call.message, booking_id)
    elif data.startswith("quick_cancel_"):
        booking_id = data.split("_")[2]
        quick_cancel_booking(call.message, booking_id)
    elif data.startswith("confirm_quick_cancel_"):
        booking_id = data.split("_")[3]
        finalize_quick_cancel_booking(call.message, booking_id)
    elif data.startswith("edit_booking_"):
        booking_id = data.split("_")[2]
        edit_booking_date(call.message, booking_id)
    elif data.startswith("edit_date_"):
        parts = data.split("_")
        booking_id, new_date = parts[2], parts[3]
        edit_booking_time_selection(call.message, booking_id, new_date)
    elif data.startswith("edit_time_"):
        parts = data.split("_")
        booking_id, new_date, new_time = parts[2], parts[3], parts[4]
        markup = types.InlineKeyboardMarkup()
        btn_confirm = types.InlineKeyboardButton("✅ Подтвердить изменение", callback_data=f"confirm_edit_{booking_id}_{new_date}_{new_time}")
        btn_back = types.InlineKeyboardButton("⬅ Назад", callback_data=f"edit_date_{booking_id}_{new_date}")
        markup.row(btn_confirm, btn_back)
        text = f"Вы выбрали новую **дату**: *{new_date}*\nи новое **время**: *{new_time}*\n\nПодтвердите изменение брони."
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        except:
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
    elif data.startswith("confirm_edit_"):
        parts = data.split("_")
        booking_id, new_date, new_time = parts[2], parts[3], parts[4]
        finalize_edit_booking(call.message, booking_id, new_date, new_time)
    elif data.startswith("contact_"):
        booking_id = data.split("_")[1]
        prompt_contact_admin(call.message, booking_id)
    elif data.startswith("review_"):
        booking_id = data.split("_")[1]
        booking_review(call.message, booking_id)
    
    # Отзывы о квестах
    elif data.startswith("quest_reviews_"):
        quest_id = data.split("_")[2]
        show_quest_reviews(call.message, quest_id)
    elif data.startswith("quest_add_review_"):
        quest_id = data.split("_")[3]
        msg = bot.send_message(
            call.message.chat.id, 
            f"⭐ Напишите ваш отзыв о квесте:\n\nМаксимальная длина - 500 символов."
        )
        bot.register_next_step_handler(msg, process_quest_review, quest_id)
    
    # Просмотр акции
    elif data.startswith("promo_"):
        promo_id = data.split("_")[1]
        show_promotion_detail(call.message, promo_id, call.message.message_id)
    
    # Обработка кнопки "Назад" для информации о квесте
    elif data.startswith("back_info_"):
        parts = data.split("_")
        quest_type = parts[2]
        
        if quest_type == "kids":
            show_quest_list(call.message, quest_type="kids")
        else:
            if len(parts) > 3:
                genre = parts[3]
                show_quest_list(call.message, quest_type="adults", genre=genre)
            else:
                show_adult_genres(call.message)
    
    else:
        bot.answer_callback_query(call.id, "ℹ️ Команда не распознана")

def process_quest_review(message, quest_id):
    """Сохранение отзыва о квесте"""
    if len(message.text) > 500:
        bot.send_message(
            message.chat.id, 
            "❌ Отзыв слишком длинный. Максимум 500 символов."
        )
        return
        
    user_id = message.chat.id
    review_text = message.text
    
    # Добавляем пользователя в базу
    ensure_user_exists(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    try:
        query = "INSERT INTO reviews (user_id, review, created_at) VALUES (%s, %s, NOW())"
        cursor.execute(query, (user_id, review_text))
        conn.commit()
        
        bot.send_message(
            message.chat.id, 
            "✅ Спасибо! Ваш отзыв сохранён."
        )
        
        # Уведомление администратору
        bot.send_message(
            ADMIN_ID, 
            f"⭐ Новый отзыв от {message.from_user.first_name} (ID: {user_id}) о квесте ID {quest_id}:\n\n{review_text}"
        )
        
    except Exception as e:
        logging.error(f"Ошибка при сохранении отзыва: {str(e)}")
        bot.send_message(
            message.chat.id, 
            "❌ Произошла ошибка при сохранении отзыва."
        )

# Уведомление о предстоящем квесте
def send_upcoming_quest_notifications():
    while True:
        try:
            now = datetime.now()
            notify_time = now + timedelta(hours=3)
            
            query = """
                SELECT b.id, u.id, q.name, b.date, b.time 
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN circles q ON b.quest_id = q.id
                WHERE b.status = 'confirmed'
                AND b.date = %s
                AND b.time BETWEEN %s AND %s
            """
            cursor.execute(query, (notify_time.date(), (notify_time - timedelta(minutes=5)).time(), notify_time.time()))
            bookings = cursor.fetchall()
            
            for booking in bookings:
                booking_id, user_id, quest_name, date, time_slot = booking
                text = (
                    f"⏰ *Напоминание о бронировании!*\n\n"
                    f"Через 3 часа у вас запланирован квест:\n"
                    f"🎮 *Квест:* {quest_name}\n"
                    f"📅 *Дата:* {date}\n"
                    f"⏰ *Время:* {time_slot}\n\n"
                    f"Пожалуйста, не опаздывайте!"
                )
                bot.send_message(user_id, text, parse_mode="Markdown")
            
            time.sleep(60)  # Проверка каждую минуту
            
        except Exception as e:
            logging.error(f"Ошибка в уведомлениях: {str(e)}")
            time.sleep(60)

# Запуск потока для уведомлений
notification_thread = threading.Thread(target=send_upcoming_quest_notifications)
notification_thread.daemon = True
notification_thread.start()

# ---------------------- ЗАПУСК БОТА ----------------------
if __name__ == "__main__":
    print("Бот запущен...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(f"Ошибка polling: {e}")
            print(f"Ошибка polling: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)