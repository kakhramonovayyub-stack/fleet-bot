import os
import telebot
import pytesseract
from PIL import Image

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

    # download image
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("receipt.jpg", 'wb') as f:
        f.write(downloaded_file)

    # OCR
    try:
        img = Image.open("receipt.jpg")
        text = pytesseract.image_to_string(img)
    except Exception as e:
        text = f"OCR FAILED: {e}"

    bot.send_message(ADMIN_ID, f"""
Driver: {driver}
Truck: {truck}

RAW OCR TEXT:
{text[:1000]}
""")

print("Bot started...")
bot.infinity_polling(timeout=30, long_polling_timeout=20)
