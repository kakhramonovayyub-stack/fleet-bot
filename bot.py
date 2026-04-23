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

    # ---- LOCATION (IMPROVED) ----
    for line in lines:
        if "," in line and len(line) < 50:
            data["location"] = line.strip()

    # ---- TOTAL ----
    total_match = re.search(r"Total\s*(\d+\.\d+)", text)
    if total_match:
        data["total"] = total_match.group(1)

    # ---- GALLONS (diesel + DEF) ----
    gallons = re.findall(r"Gallons:\s*(\d+\.\d+)", text)
    if gallons:
        data["diesel_gal"] = gallons[0]
    if len(gallons) > 1:
        data["def_gal"] = gallons[1]

    # ---- DIESEL PRICE ----
    diesel_price = re.search(r"Price\s*/\s*Gal:\s*(\d+\.\d+)", text)
    if diesel_price:
        data["diesel_price"] = diesel_price.group(1)

    # ---- DIESEL TOTAL ----
    diesel_total = re.search(r"DIE.*?(\d+\.\d+)", text, re.IGNORECASE)
    if diesel_total:
        data["diesel_total"] = diesel_total.group(1)

    # ---- DEF TOTAL (STRONG FIX) ----
    def_total = re.search(r"DEF\s*(\d+\.\d+)", text, re.IGNORECASE)
    if def_total:
        val = def_total.group(1)

        # avoid picking main total
        if data["total"]:
            if abs(float(val) - float(data["total"])) > 1:
                data["def_total"] = val

    return data

# -------------------------------
# HANDLE PHOTO (MAIN LOGIC)
# -------------------------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    # Download image
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

    # Extract structured data
    data = extract_data(text)

    # Send to admin
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
