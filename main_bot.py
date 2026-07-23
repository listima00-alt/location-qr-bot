import os
import time
import telebot
import qrcode

# ================= CONFIGURATION =================
BOT_TOKEN = "8705116326:AAHKAtaGKPOEWnw-KlkdX6EPf_W_3vizsHE"
ALLOWED_CHAT_ID = 7230777890

DEVELOPER_NAME = "Taaj"
# =================================================

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        bot.reply_to(message, f"⚠️ Access Denied! Chat ID `{message.chat.id}` authorized nahi hai.", parse_mode="Markdown")
        return
    
    bot.reply_to(
        message,
        f"📍 **Welcome to Location QR Code Generator Bot!**\n"
        f"👨‍💻 *Created by: {DEVELOPER_NAME}*\n\n"
        "Mujhe aap:\n"
        "1. Kisi jagah ka **Google Maps Link / Address** bhej sakte hain.\n"
        "2. Telegram ka **Location Pin** share kar sakte hain.\n\n"
        "Main turant scan-able QR Code banakar bhej dunga!",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=['location'])
def handle_location_pin(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return

    lat = message.location.latitude
    lon = message.location.longitude
    
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    generate_and_send_qr(message, maps_url, f"📍 **Location Coordinates:**\n`Lat: {lat}, Lon: {lon}`")


@bot.message_handler(func=lambda message: True)
def handle_text_location(message):
    if message.chat.id != ALLOWED_CHAT_ID:
        return

    text_input = message.text.strip()

    if not text_input.startswith("http://") and not text_input.startswith("https://"):
        maps_url = f"https://www.google.com/maps/search/?api=1&query={text_input.replace(' ', '+')}"
    else:
        maps_url = text_input

    generate_and_send_qr(message, maps_url, f"📌 **Location Link:**\n`{text_input}`")


def generate_and_send_qr(message, data_to_encode, caption_text):
    status_msg = bot.reply_to(message, "⏳ Location ka QR Code generate ho raha hai...")

    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_to_encode)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        file_path = f"loc_qr_{message.chat.id}.png"
        img.save(file_path)

        with open(file_path, 'rb') as photo:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=(
                    f"✅ **Location QR Code Ready!**\n\n"
                    f"{caption_text}\n\n"
                    f"✨ *Bot Created by: {DEVELOPER_NAME}*"
                ),
                parse_mode="Markdown"
            )

        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        bot.reply_to(message, f"❌ Error aaya: {e}")


if __name__ == "__main__":
    print(f"🚀 Bot successfully start ho gaya hai (Developer: {DEVELOPER_NAME})...")
    
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"⚠️ Connection error: {e}")
            time.sleep(3)
          
