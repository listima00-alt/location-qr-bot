import logging
import qrcode
import io
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = "8705116326:AAHKAtaGKPOEWnw-KlkdX6EPf_W_3vizsHE"
TMDB_API_KEY = "8415442e3f538e14e1f76d91f24d3a1f"  # Free TMDB Key

# 👑 Tajdar Bhai Details & Instagram Link
OWNER_NAME = "Tajdar"  
INSTAGRAM_PROFILE_URL = "https://www.instagram.com/vacio.__x?igsh=MWtlczUwYjducG9j"
# ========================================================

# Users ka Follow verification state track karne ke liye
USER_VERIFIED = set()

def get_follow_keyboard():
    keyboard = [
        [InlineKeyboardButton("📸 Follow Tajdar on Instagram", url=INSTAGRAM_PROFILE_URL)],
        [InlineKeyboardButton("🔓 Verify / Unlock Bot", callback_data="check_follow")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def check_user_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if user_id in USER_VERIFIED:
        return True

    text = (
        f"🔒 **Bot Is Locked!**\n\n"
        f"Hello {update.effective_user.first_name}! Is bot ko use karne ke liye aapko pehle **{OWNER_NAME}** ko Instagram par follow karna zaroori hai.\n\n"
        f"1️⃣ Niche diye gaye **Instagram** button par click karke follow karein.\n"
        f"2️⃣ Follow karne ke baad **Verify / Unlock Bot** button dabaaein."
    )
    
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_follow_keyboard())
    return False

# Verification Callback Handler
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    USER_VERIFIED.add(user_id)

    success_text = (
        f"🎉 **Thank You For Following!**\n\n"
        f"Aapka Bot unlock ho gaya hai! Ab aap Tajdar ke Super Bot ke features use kar sakte hain:\n\n"
        f"📸 **QR Code:** Koi bhi text ya link bhejye.\n"
        f"🍿 **Movie Search:** `/movie [movie name]` likhein."
    )
    
    keyboard = [[InlineKeyboardButton(f"👑 Bot Owner: {OWNER_NAME}", url=INSTAGRAM_PROFILE_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=reply_markup)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_access(update, context):
        return

    welcome_text = (
        f"👋 **Welcome to Tajdar's Super Bot!**\n\n"
        f"📸 **QR Code Banane ke liye:** Koi bhi text ya link bhejye.\n"
        f"🍿 **Movie Search ke liye:** `/movie [movie name]` likhein.\n"
        f"   *(Example: `/movie Pushpa 2`)*\n\n"
        f"👑 **Bot Owner:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})"
    )
    
    keyboard = [[InlineKeyboardButton(f"👑 Developer: {OWNER_NAME}", url=INSTAGRAM_PROFILE_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True)

# 1. QR Code Generator Function
async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if user_text.lower().startswith("/movie"):
        return

    if not await check_user_access(update, context):
        return

    status_msg = await update.message.reply_text("⏳ Aapka QR code ban raha hai...")

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(user_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)

    caption = (
        f"✅ **Aapka QR Code Tayar Hai!**\n\n"
        f"🛠️ **Powered By:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})"
    )
    
    keyboard = [[InlineKeyboardButton(f"👑 Bot Owner: {OWNER_NAME}", url=INSTAGRAM_PROFILE_URL)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await status_msg.delete()
    await update.message.reply_photo(photo=bio, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)

# 2. Movie Downloader Function (/movie Name)
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user_access(update, context):
        return

    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text("❌ Kripya movie ka naam bhi likhein!\nExample: `/movie Jawan`", parse_mode="Markdown")
        return

    status_msg = await update.message.reply_text("🍿 Movie dhoond raha hu, bas 2 second...")

    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url).json()
    results = response.get('results', [])

    if not results:
        await status_msg.edit_text("❌ Maf karna, ye movie nahi mili! Spelling check karke dobara try karein.")
        return

    movie = results[0]
    title = movie.get('title', 'N/A')
    overview = movie.get('overview', 'No description available.')
    release_date = movie.get('release_date', 'N/A')
    rating = movie.get('vote_average', 'N/A')
    poster_path = movie.get('poster_path')

    await status_msg.delete()

    google_search_url = f"https://www.google.com/search?q=download+{title.replace(' ', '+')}+movie+full+hd"
    telegram_search_url = f"https://t.me/s/{title.replace(' ', '_')}_movies"
    youtube_trailer_url = f"https://www.youtube.com/results?search_query={title.replace(' ', '+')}+official+trailer"

    caption = (
        f"🍿 **{title}** ({release_date[:4] if release_date != 'N/A' else 'N/A'})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ **IMDb Rating:** `{rating}/10`\n"
        f"📝 **Story:** {overview[:170]}...\n\n"
        f"👑 **Powered By:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})\n"
        f"👇 **Niche se download ya trailer dekhein:**"
    )

    keyboard = [
        [InlineKeyboardButton("🎬 Watch Trailer (YouTube)", url=youtube_trailer_url)],
        [InlineKeyboardButton("📥 Fast Download (480p / 720p / 1080p)", url=google_search_url)],
        [InlineKeyboardButton("🚀 Telegram Channel Direct Search", url=telegram_search_url)],
        [InlineKeyboardButton(f"👑 Bot Owner: {OWNER_NAME}", url=INSTAGRAM_PROFILE_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if poster_path:
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        await update.message.reply_photo(photo=image_url, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=reply_markup, disable_web_page_preview=True)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", search_movie))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^check_follow$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_qr))

    print("Tajdar's Insta-Protected Bot Live!")
    app.run_polling()

if __name__ == "__main__":
    main()
