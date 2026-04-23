import os
import telebot
import pytesseract
from PIL import Image
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# -------------------------------
# GOOGLE SHEETS SETUP
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1BlRwYLhyMAzZNtadmglOCL19ACwKfYf0j_XaLtR9msQ/edit?usp=sharing").sheet1

# store last receipt
last_data = {}

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
# EXTRACT DATA
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

    # LOCATION
    for line in lines:
        line = line.strip()
        match = re.search(r"([A-Za-z\s]+)[,\.]?\s+([A-Z]{2})", line)
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            if len(city) > 3 and city.lower() not in ["total", "invoice", "pump"]:
                data["location"] = f"{city}, {state}"
                break

    # TOTAL
    total_match = re.search(r"Total\s*(\d+\.\d+)", text)
    if total_match:
        data["total"] = total_match.group(1)

    # GALLONS (OCR FIX)
    gallons = re.findall(r"Gal\s*lons:\s*(\d+\.\d+)", text, re.IGNORECASE)

    if len(gallons) >= 2:
        nums = [float(g) for g in gallons]
        data["diesel_gal"] = str(max(nums))
        data["def_gal"] = str(min(nums))
    elif gallons:
        data["diesel_gal"] = gallons[0]

    # PRICE
    price_match = re.search(r"Price\s*/\s*Gal:\s*(\d+\.\d+)", text)
    if price_match:
        data["diesel_price"] = price_match.group(1)

    # DIESEL TOTAL
    diesel_total_match = re.search(r"DIE.*?(\d+\.\d+)", text, re.IGNORECASE)
    if diesel_total_match:
        data["diesel_total"] = diesel_total_match.group(1)

    # DEF TOTAL
    def_match = re.search(r"DEF\s*(\d+\.\d+)", text, re.IGNORECASE)
    if def_match:
        val = float(def_match.group(1))
        if data["total"] and abs(val - float(data["total"])) > 1:
            data["def_total"] = str(val)

    # CLEAN
    data["diesel_gal"] = clean(data["diesel_gal"])
    data["diesel_price"] = clean(data["diesel_price"])
    data["diesel_total"] = clean(data["diesel_total"])
    data["def_gal"] = clean(data["def_gal"])
    data["def_total"] = clean(data["def_total"])
    data["total"] = clean(data["total"])

    return data

# -------------------------------
# HANDLE PHOTO
# -------------------------------
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    global last_data

    if message.chat.type not in ['group', 'supergroup']:
        return

    group_name = message.chat.title
    driver, truck = parse_group_name(group_name)

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("receipt.jpg", "wb") as f:
        f.write(downloaded_file)

    try:
        img = Image.open("receipt.jpg")
        text = pytesseract.image_to_string(img)
    except Exception as e:
        bot.send_message(ADMIN_ID, f"OCR FAILED: {e}")
        return

    data = extract_data(text)

    # store for confirmation
    last_data = {
        "driver": driver,
        "truck": truck,
        "location": data['location'],
        "diesel_gal": data['diesel_gal'],
        "price": data['diesel_price'],
        "diesel_total": data['diesel_total'],
        "def": data['def_total'],
        "total": data['total']
    }

    bot.send_message(ADMIN_ID, f"""
New Fuel Receipt:

Driver: {driver}
Truck: {truck}

Location: {data['location']}

Diesel: {data['diesel_gal']} gal @ {data['diesel_price']} = {data['diesel_total']}
DEF: {data['def_gal']} = {data['def_total']}

Total: {data['total']}

Reply: YES / NO
""")

# -------------------------------
# HANDLE YES / NO
# -------------------------------
@bot.message_handler(func=lambda m: m.text in ["YES", "NO"])
def handle_confirmation(message):
    global last_data

    if message.text == "YES":
        try:
            sheet.append_row([
                str(message.date),
                last_data["driver"],
                last_data["truck"],
                last_data["location"],
                last_data["diesel_gal"],
                last_data["price"],
                last_data["diesel_total"],
                last_data["def"],
                last_data["total"]
            ])

            bot.send_message(message.chat.id, "✅ Saved to Google Sheets")

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error: {e}")

    else:
        bot.send_message(message.chat.id, "❌ Ignored")

# -------------------------------
# START BOT
# -------------------------------
print("Bot started...")
bot.infinity_polling(timeout=30, long_polling_timeout=20)
