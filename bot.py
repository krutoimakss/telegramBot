import telebot

BOT_TOKEN = "8927675557:AAG6K-9NWxJa7RYPcrwQRPLcERMGx1H_7oE"
CHANNEL_ID = "-1002064908340"  # или числовой ID

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(func=lambda message: True)
def forward_to_channel(message):
    try:
        bot.forward_message(CHANNEL_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ Отправлено в канал!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

bot.polling()
