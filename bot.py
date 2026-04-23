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

    # ---- LOCATION ----
    for line in lines:
        if "," in line and len(line) < 40:
            if any(state in line for state in ["AR", "TX", "OK", "CA", "NM"]):
                data["location"] = line.strip()

    # ---- TOTAL ----
    total_match = re.search(r"Total\s*(\d+\.\d+)", text)
    if total_match:
        data["total"] = total_match.group(1)

    # ---- DIESEL ----
    diesel_block = re.search(r"DIE.*?Gallons:\s*(\d+\.\d+).*?Price\s*/\s*Gal:\s*(\d+\.\d+).*?(\d+\.\d+)", text, re.DOTALL | re.IGNORECASE)
    if diesel_block:
        data["diesel_gal"] = diesel_block.group(1)
        data["diesel_price"] = diesel_block.group(2)
        data["diesel_total"] = diesel_block.group(3)

    # ---- DEF ----
    def_block = re.search(r"DEF.*?Gallons:\s*(\d+\.\d+).*?(\d+\.\d+)", text, re.DOTALL | re.IGNORECASE)
    if def_block:
        data["def_gal"] = def_block.group(1)
        data["def_total"] = def_block.group(2)

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
