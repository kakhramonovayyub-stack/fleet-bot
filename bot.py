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

    # ---- FIND ALL GALLONS ----
    gallons = re.findall(r"Gallons:\s*(\d+\.\d+)", text)

    if len(gallons) >= 2:
        g1 = float(gallons[0])
        g2 = float(gallons[1])

        if g1 > g2:
            data["diesel_gal"] = str(g1)
            data["def_gal"] = str(g2)
        else:
            data["diesel_gal"] = str(g2)
            data["def_gal"] = str(g1)

    # ---- DIESEL PRICE ----
    price_match = re.search(r"Price\s*/\s*Gal:\s*(\d+\.\d+)", text)
    if price_match:
        data["diesel_price"] = price_match.group(1)

    # ---- TOTAL VALUES ----
    totals = re.findall(r"\b(\d+\.\d{2})\b", text)
    filtered = [t for t in totals if t != data["total"]]

    if len(filtered) >= 2:
        nums = sorted([float(x) for x in filtered])
        data["def_total"] = str(nums[0])
        data["diesel_total"] = str(nums[-1])

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
