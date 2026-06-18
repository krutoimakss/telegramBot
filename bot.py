import telebot
from telebot import types

BOT_TOKEN = "8927675557:AAG6K-9NWxJa7RYPcrwQRPLcERMGx1H_7oE"  # Смените токен! Старый скомпрометирован
CHANNEL_ID = "-1002064908340"
OWNER_ID = 6271603562

bot = telebot.TeleBot(BOT_TOKEN)

# ──────────────────────────────────────────
#  Хранилище состояний (в памяти)
# ──────────────────────────────────────────
ACCESS_CODE      = "0000AAAA"       # Код по умолчанию
authenticated    = set()            # user_id прошедших проверку
blacklist        = set()            # username'ы (строчные, без @)
admins           = {OWNER_ID}       # user_id администраторов
all_users        = set()            # все известные user_id (для рассылки)
pending_admins   = set()            # username'ы ожидающих назначения
waiting_for      = {}               # user_id -> действие (многошаговый ввод)


# ──────────────────────────────────────────
#  Вспомогательные функции
# ──────────────────────────────────────────
def is_banned(message) -> bool:
    uname = (message.from_user.username or "").lower()
    return uname in blacklist

def is_auth(user_id) -> bool:
    return user_id in authenticated

def check_access(message) -> bool:
    """Проверяет бан и авторизацию. Возвращает True если можно продолжать."""
    uid = message.from_user.id
    all_users.add(uid)

    if is_banned(message):
        bot.reply_to(message, "❗Ты Был забанен в этом боте и ты больше не сможешь ним пользоватся")
        return False

    if not is_auth(uid):
        bot.reply_to(
            message,
            "🔒 Вход Закрыт чтобы продолжить введите код\n"
            "Код должен выглядить потипу так: 0000AAAA"
        )
        return False

    # Назначение ожидающего администратора при первом сообщении
    uname = (message.from_user.username or "").lower()
    if uname in pending_admins:
        admins.add(uid)
        pending_admins.discard(uname)
        bot.send_message(uid, "🏅 Вы были назначены администратором!")

    return True


# ──────────────────────────────────────────
#  /start
# ──────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    all_users.add(uid)

    if is_banned(message):
        bot.reply_to(message, "❗Ты Был забанен в этом боте и ты больше не сможешь ним пользоватся")
        return

    if is_auth(uid):
        bot.send_message(uid, "✅ Вы уже авторизованы!")
    else:
        bot.send_message(
            uid,
            "🔒 Вход Закрыт чтобы продолжить введите код\n"
            "Код должен выглядить потипу так: 0000AAAA"
        )


# ──────────────────────────────────────────
#  /info
# ──────────────────────────────────────────
@bot.message_handler(commands=["info"])
def cmd_info(message):
    if not check_access(message):
        return
    bot.reply_to(message, "✅ Бот работает в штатном режиме!")


# ──────────────────────────────────────────
#  /message
# ──────────────────────────────────────────
@bot.message_handler(commands=["message"])
def cmd_message(message):
    if not check_access(message):
        return

    text = message.text[len("/message"):].strip()
    if not text:
        bot.reply_to(message, "❌ Укажите текст: /message ваш текст")
        return

    try:
        bot.send_message(CHANNEL_ID, text)
        bot.reply_to(message, "✅ Сообщение отправлено в канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


# ──────────────────────────────────────────
#  /adminpanel
# ──────────────────────────────────────────
@bot.message_handler(commands=["adminpanel"])
def cmd_adminpanel(message):
    uid = message.from_user.id
    all_users.add(uid)

    if uid not in admins:
        return  # Молчаливое игнорирование

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔑 Изменить Код",            callback_data="change_code"),
        types.InlineKeyboardButton("📒 Черный Список",            callback_data="blacklist"),
        types.InlineKeyboardButton("🌐 Глобальное Сообщение",     callback_data="global_msg"),
        types.InlineKeyboardButton("🏅 Назначить Администратором", callback_data="assign_admin"),
    )
    bot.send_message(uid, "🧰 Здравствуйте Разработчик вот все админ меню", reply_markup=markup)


# ──────────────────────────────────────────
#  Обработка кнопок админ-панели
# ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)

    if uid not in admins:
        return

    prompts = {
        "change_code":   "🔑 Напишите Новый код пожалуйста",
        "blacklist":     "📒 Напиши Юзернейм того кого вы хотите поместить в черный список",
        "global_msg":    "🌐 Напишите Сообщение которое прислется всем",
        "assign_admin":  "🏅 Кого Вы хотите назначить администратором тоесть напишите юзернейм",
    }

    if call.data in prompts:
        waiting_for[uid] = call.data
        bot.send_message(uid, prompts[call.data])


# ──────────────────────────────────────────
#  Главный обработчик всех сообщений
# ──────────────────────────────────────────
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    global ACCESS_CODE

    uid   = message.from_user.id
    uname = (message.from_user.username or "").lower()
    all_users.add(uid)

    # ── Бан ──
    if is_banned(message):
        bot.reply_to(message, "❗Ты Был забанен в этом боте и ты больше не сможешь ним пользоватся")
        return

    # ── Многошаговый ввод для администратора ──
    if uid in waiting_for:
        action = waiting_for.pop(uid)
        text   = message.text.strip()

        if action == "change_code":
            ACCESS_CODE = text
            authenticated.clear()   # Выкидываем всех
            bot.reply_to(message, f"✅ Код изменён на: {ACCESS_CODE}\nВсе пользователи были выкинуты.")

        elif action == "blacklist":
            target = text.lstrip("@").lower()
            blacklist.add(target)
            bot.reply_to(message, f"✅ @{target} добавлен в черный список.")

        elif action == "global_msg":
            broadcast = f"🧇 **СРОЧНОЕ СООБЩЕНИЕ**\n{text}"
            sent = 0
            for recv_id in list(all_users):
                try:
                    bot.send_message(recv_id, broadcast, parse_mode="Markdown")
                    sent += 1
                except Exception:
                    pass
            bot.reply_to(message, f"✅ Сообщение отправлено {sent} пользователям.")

        elif action == "assign_admin":
            target = text.lstrip("@").lower()
            pending_admins.add(target)
            bot.reply_to(message, f"✅ @{target} будет назначен администратором при следующем сообщении боту.")

        return

    # ── Проверка кода (для неавторизованных) ──
    if not is_auth(uid):
        if message.text.strip() == ACCESS_CODE:
            authenticated.add(uid)
            # Назначение ожидающего admin
            if uname in pending_admins:
                admins.add(uid)
                pending_admins.discard(uname)
                bot.reply_to(message, "✅ Код верный! Добро пожаловать!\n🏅 Вы также были назначены администратором!")
            else:
                bot.reply_to(message, "✅ Код верный! Добро пожаловать!")
        else:
            bot.reply_to(
                message,
                "🔒 Вход Закрыт чтобы продолжить введите код\n"
                "Код должен выглядить потипу так: 0000AAAA"
            )
        return

    # ── Назначение ожидающего admin при обычном сообщении ──
    if uname in pending_admins:
        admins.add(uid)
        pending_admins.discard(uname)
        bot.send_message(uid, "🏅 Вы были назначены администратором!")

    # ── Пересылка сообщения в канал ──
    try:
        bot.forward_message(CHANNEL_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ Отправлено в канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


bot.polling(none_stop=True)
