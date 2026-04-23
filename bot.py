# OCR VERSION FORCE
import pytesseract
from PIL import Image

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
    except:
        text = "OCR FAILED"

    bot.send_message(ADMIN_ID, f"""
Driver: {driver}
Truck: {truck}

RAW OCR TEXT:
{text[:1000]}
""")
