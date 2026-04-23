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

    # assign biggest to diesel
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

    # ---- ALL TOTAL VALUES ----
    totals = re.findall(r"\b(\d+\.\d{2})\b", text)

    # remove main total
    filtered = [t for t in totals if t != data["total"]]

    # biggest = diesel, smallest = DEF
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
# START BOT
# -------------------------------
print("Bot started...")
bot.infinity_polling(timeout=30, long_polling_timeout=20)
