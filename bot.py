import os
import telebot
import pytesseract
from PIL import Image
import re

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# -------------------------------
# PARSE GROUP NAME
# -------------------------------
def parse_group_name(name):
    try:
        driver, truck = name.split("/")
        return driver.strip(), truck.strip()
    except:
        return name, "Unknown"

# -------------------------------
# CLEAN NUMBERS
# -------------------------------
def clean(val):
    try:
        return str(round(float(val), 2))
    except:
        return val

# -------------------------------
# EXTRACT DATA FROM OCR TEXT
# -------------------------------
def extract_data(text):
    data = {
        "diesel_gal": "",
        "diesel_price": "",
        "diesel_total": "",
        "def_gal": "",
        "def_total": "",
        "total": "",
        "location": ""
    }

    text = text.replace(",", ".")
    lines = text.split("\n")

    # ---- LOCATION ----
    for line in lines:
        if re.search(r"[A-Za-z]+\s*,\s*[A-Z]{2}", line):
            data["location"] = line.strip()
            break

    # ---- TOTAL ----
    total_match = re.search(r"Total\s*(\d+\.\d+)", text)
    if total_match:
        data["total"] = total_match.group(1)

    # ---- DIESEL GALLONS ----
    diesel_gal_match = re.search(r"Gallons:\s*(\d+\.\d+)", text)
    if diesel_gal_match:
        data["diesel_gal"] = diesel_gal_match.group(1)

    # ---- DEF GALLONS ----
    def_gal_match = re.search(r"DEF.*?Gallons:\s*(\d+\.\d+)", text, re.DOTALL | re.IGNORECASE)
    if def_gal_match:
        data["def_gal"] = def_gal_match.group(1)

    # ---- DIESEL PRICE ----
    price_match = re.search(r"Price\s*/\s*Gal:\s*(\d+\.\d+)", text)
    if price_match:
        data["diesel_price"] = price_match.group(1)

    # ---- DIESEL TOTAL ----
    diesel_total_match = re.search(r"DIE.*?(\d+\.\d+)", text, re.IGNORECASE)
    if diesel_total_match:
        data["diesel_total"] = diesel_total_match.group(1)

    # ---- DEF TOTAL ----
    def_total_match = re.search(r"DEF\s*(\d+\.\d+)", text, re.IGNORECASE)
    if def_total_match:
        val = def_total_match.group(1)

        # prevent picking main total
        if data["total"] and float(val) != float(data["total"]):
            data["def_total"] = val

    # ---- CLEAN ----
    data["diesel_gal"] = clean(data["diesel_gal"])
    data["diesel_price"] = clean(data["diesel_price"])
    data["diesel_total"] = clean(data["diesel_total"])
    data["def_gal"] = clean(data["def_gal"])
    data["def_total"] = clean(data["def_total"])
    data["total"] = clean(data["total"])

    return data

# -------------------------------
# HANDLE PHOTO (YOU MISSED THIS)
# -------------------------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    # download image
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("receipt.jpg", "wb") as f:
        f.write(downloaded_file)

    # OCR
    try:
        img = Image.open("receipt.jpg")
        text = pytesseract.image_to_string(img)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"OCR FAILED: {e}")
        return

    data = extract_data(text)

    bot.send_message(ADMIN_ID, f"""
New Fuel Receipt:

Driver: {driver}
Truck: {truck}

Location: {data['location']}

Diesel: {data['diesel_gal']} gal @ {data['diesel_price']} = {data['diesel_total']}
DEF: {data['def_gal']} = {data['def_total']}

Total: {data['total']}

Reply: YES / NO / EDIT
""")

# -------------------------------
# START BOT
# -------------------------------
print("Bot started...")
bot.infinity_polling(timeout=30, long_polling_timeout=20)
