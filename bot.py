# OCR version 2
import os
import telebot
import pytesseract
from PIL import Image
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

def extract_text(file_path):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text

def simple_parse(text):
    data = {
        "date": "Unknown",
        "location": "Unknown",
        "station": "Unknown",
        "diesel_gal": "0",
        "diesel_price": "0",
        "diesel_total": "0",
        "def_gal": "0",
        "def_price": "0",
        "def_total": "0",
        "total": "0"
    }

    lines = text.split("\n")

    for line in lines:
        if "DIESEL" in line.upper():
            data["station"] = "Fuel Station"
        if "TOTAL" in line.upper():
            data["total"] = line.split()[-1]

    return data

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("receipt.jpg", 'wb') as f:
        f.write(downloaded_file)

    text = extract_text("receipt.jpg")
    data = simple_parse(text)

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

import time

while True:
    try:
        print("Bot started...")
        bot.polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
