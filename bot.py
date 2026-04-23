import os
import telebot
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

def parse_group_name(name):
    try:
        driver, truck = name.split("/")
        return driver.strip(), truck.strip()
    except:
        return name, "Unknown"

def fake_parse_receipt():
    # TEMP (we will replace with real OCR next)
    return {
        "date": "Auto",
        "location": "Auto",
        "station": "Love's",
        "diesel_gal": "100",
        "diesel_price": "5.00",
        "diesel_total": "500",
        "def_gal": "5",
        "def_price": "4.00",
        "def_total": "20",
        "total": "520"
    }

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    data = fake_parse_receipt()

    caption = f"""
New Fuel Receipt:

Driver: {driver}
Truck: {truck}

Date: {data['date']}
Location: {data['location']}
Gas Station: {data['station']}

Diesel: {data['diesel_gal']} gal @ {data['diesel_price']} = {data['diesel_total']}
DEF: {data['def_gal']} gal @ {data['def_price']} = {data['def_total']}

Total: {data['total']}

Reply: YES / NO / EDIT
"""

    bot.send_message(ADMIN_ID, caption)

bot.infinity_polling()
