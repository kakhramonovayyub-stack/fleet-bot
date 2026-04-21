import os
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

def parse_group_name(name):
    try:
        driver, truck = name.split("/")
        return driver.strip(), truck.strip()
    except:
        return name, "Unknown"

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    caption = f"""
New Fuel Receipt:

Driver: {driver}
Truck: {truck}

(Receipt parsing coming next step)

Reply: YES / NO
"""

    bot.send_message(ADMIN_ID, caption)

bot.infinity_polling()
