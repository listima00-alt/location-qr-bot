import os
import requests
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ----------------- CONFIGURATION -----------------
TELEGRAM_BOT_TOKEN = "7913890604:AAHBJGee__kK1WUZsFJexKFRrKIlZ3OZZrQ"  # Updated New Token
TMDB_API_KEY = "388db44a86782a4d952a22be14bd2db1"                       # TMDB API Key
INSTAGRAM_USERNAME = "vacio.__x"
INSTAGRAM_PROFILE_URL = f"https://www.instagram.com/{INSTAGRAM_USERNAME}/"
OWNER_NAME = "Tajdar"
# -------------------------------------------------


# Helper function to check/force Instagram restriction
async def check_instagram_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    is_verified = context.user_data.get("insta_verified", False)

    if not is_verified:
        keyboard = [
            [InlineKeyboardButton("👉 Follow Instagram Profile 👈", url=INSTAGRAM_PROFILE_URL)],
            [InlineKeyboardButton("✅ Unlocked / Verified", callback_data="verify_follow")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        text = (
            f"⚠️ **Access Restricted!** ⚠️\n\n"
            f"Tajdar's Bot ko use karne ke liye pehle Instagram par **@{INSTAGRAM_USERNAME}** ko follow karein!\n\n"
            f"1️⃣ Upar link par click karke follow karein.\n"
            f"2️⃣ Phir **Unlocked / Verified** button par tap karein."
        )

        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        return False
    return True


# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_instagram_lock(update, context):
        return

    welcome_text = (
        f"👑 **Welcome to {OWNER_NAME}'s Bot!** 👑\n\n"
        f"Aapka Instagram verification ho chuka hai. ✨\n\n"
        f"📌 **Aap kya kar sakte hain:**\n"
        f"1. **QR Code Generator:** Mujhe koi bhi Text ya Link bhejo, main uska QR Code bana dunga.\n"
        f"2. **Movie Search:** Type karein `/movie <Movie Name>` (e.g., `/movie Pushpa 2`)\n\n"
        f"🔥 **Owner Profile:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", disable_web_page_preview=True)


# Verification Callback Button
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["insta_verified"] = True
    await query.message.edit_text(
        "🎉 **Verification Successful!** 🎉\n\n"
        "Aapka access unlock ho gaya hai. Ab aap bot chala sakte hain!\n"
        "Type karein `/start` ya koi bhi link/text bhej kar dekhein.",
        parse_mode="Markdown"
    )


# QR Code Generator Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_instagram_lock(update, context):
        return

    text = update.message.text
    status_msg = await update.message.reply_text("⏳ Generating QR Code...")

    # Generate QR Code in memory
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)

    await status_msg.delete()
    await update.message.reply_photo(
        photo=bio,
        caption=f"✅ **QR Code Generated Successfully!**\n\n👑 **Owner:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})",
        parse_mode="Markdown"
    )


# Movie Search Handler (TMDB)
async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_instagram_lock(update, context):
        return

    if not context.args:
        await update.message.reply_text("⚠️ **Format:** `/movie <Movie Name>`\n\n*Example:* `/movie Pushpa 2`", parse_mode="Markdown")
        return

    query_text = " ".join(context.args)
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query_text}"

    try:
        response = requests.get(url).json()
        results = response.get("results")

        if not results:
            await update.message.reply_text("❌ Koi movie nahi mili! Sahi spelling likhein.")
            return

        movie = results[0]
        title = movie.get("title", "N/A")
        overview = movie.get("overview", "No overview available.")
        rating = movie.get("vote_average", "N/A")
        release_date = movie.get("release_date", "N/A")
        poster_path = movie.get("poster_path")

        caption = (
            f"🎬 **{title}**\n\n"
            f"📅 **Release Date:** {release_date}\n"
            f"⭐ **Rating:** {rating}/10\n\n"
            f"📝 **Overview:**\n{overview[:300]}...\n\n"
            f"👑 **Powered By:** [{OWNER_NAME}]({INSTAGRAM_PROFILE_URL})"
        )

        keyboard = [
            [InlineKeyboardButton("🎬 Watch Trailer (YouTube)", url=f"https://www.youtube.com/results?search_query={title}+trailer")],
            [InlineKeyboardButton("👑 Bot Owner", url=INSTAGRAM_PROFILE_URL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if poster_path:
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            await update.message.reply_photo(photo=image_url, caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await update.message.reply_text(caption, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception:
        await update.message.reply_text("❌ Search karte me error aaya. Thodi der me try karein.")


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers Setup
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", search_movie))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_follow$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    print("Tajdar's Insta-Protected Bot Live!")
    app.run_polling()


if __name__ == '__main__':
    main()
