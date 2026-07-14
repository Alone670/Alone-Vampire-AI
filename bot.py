from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import OpenAI
from deep_translator import GoogleTranslator
import requests
import urllib.parse
import os
import yt_dlp
from config import (
    TOKEN,
    OPENROUTER_API_KEY,
)
from database import (
    create_tables,
    add_user,
    total_users,
    get_all_users,
)

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# Memory
user_memory = {}

# Image Mode
image_mode = {}

# Translator Mode
translator_mode = {}

downloader_mode = {}

settings_mode = {}

user_settings = {}


# Keyboard
keyboard = [
    ["🤖 AI Chat", "🖼️ Image Generator"],
    ["🌐 Translator", "📁 Downloader"],
    ["⚙️ Settings", "ℹ️ Help"],
]

reply_markup = ReplyKeyboardMarkup(
    keyboard,
    resize_keyboard=True,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    add_user(
        user.id,
        user.username,
        user.first_name
    )

    await update.message.reply_text(
        "👋 Welcome to Alone Vampire AI!\n\nChoose an option below:",
        reply_markup=reply_markup,
    )


ADMIN_ID = 5958566570

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    count = total_users()
    await update.message.reply_text(f"👥 Total Users: {count}")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in user_memory:
        del user_memory[user_id]

    await update.message.reply_text(
        "🗑️ Your conversation memory has been cleared.\n\n"
        "Start chatting again to begin a new conversation."
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    count = total_users()

    message = (
        "📊 AloneVampireBot Statistics\n\n"
        f"👥 Total Users: {count}\n"
        "🤖 AI Model: openai/gpt-oss-20b:free\n"
        "🗄️ Database: SQLite\n"
        "💾 Memory: Enabled\n"
        "🟢 Status: Online"
    )

    await update.message.reply_text(message)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast Your message here"
        )
        return

    message = " ".join(context.args)

    users = get_all_users()

    success = 0
    failed = 0

    for user in users:
        user_id = user[0]

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=message
            )
            success += 1

        except Exception:
            failed += 1

    await update.message.reply_text(
        f"📢 Broadcast Complete\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}"
    )

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # ================= MAIN MENU =================

    if user_text == "🤖 AI Chat":
        await update.message.reply_text("💬 Ask me anything!")
        return

    if user_text == "🖼️ Image Generator":
        image_mode[user_id] = True

        await update.message.reply_text(
            "🖼️ Image Mode Enabled!\n\n"
            "Send me an image prompt.\n\n"
            "Example:\n"
            "A vampire king sitting on a golden throne."
        )
        return

    if user_text == "🌐 Translator":
        translator_mode[user_id] = True

        await update.message.reply_text(
            "🌍 Translator Mode Enabled!\n\n"
            "Send me any text.\n\n"
            "It will be translated to English."
        )
        return

    if user_text == "📁 Downloader":
        downloader_mode[user_id] = True

        await update.message.reply_text(
            "📥 Downloader Mode Enabled!\n\n"
            "Send me a YouTube, Instagram, Facebook or TikTok link."
        )
        return

    if user_text == "⚙️ Settings":
        settings_keyboard = ReplyKeyboardMarkup(
            [
                ["🧠 Memory", "🗑️ Clear Memory"],
                ["🌐 Translate Language", "🤖 AI Model"],
                ["🎨 Image Quality", "⬅️ Back"],
            ],
            resize_keyboard=True,
        )

        await update.message.reply_text(
            "⚙️ Settings Menu",
            reply_markup=settings_keyboard,
        )
        return

    if user_text == "🧠 Memory":
        total = len(user_memory.get(user_id, []))

        await update.message.reply_text(
            f"🧠 Memory Status\n\nStored Messages: {total}"
        )
        return

    if user_text == "🗑️ Clear Memory":
        user_memory[user_id] = [
            {
                "role": "system",
                "content": "You are Alone Vampire AI. You are friendly, helpful and professional."
            }
        ]

        await update.message.reply_text(
            "✅ Memory Cleared Successfully."
        )
        return

    if user_text == "🌐 Translate Language":
        translator_mode[user_id] = True

        await update.message.reply_text(
            "🌍 Send any text.\n\nIt will be translated to English."
        )
        return

    if user_text == "🤖 AI Model":
        await update.message.reply_text(
            "🤖 Current Model:\nopenai/gpt-oss-20b:free"
        )
        return

    if user_text == "🎨 Image Quality":
        await update.message.reply_text(
            "🎨 Current Image Quality: HD"
        )
        return

    if user_text == "⬅️ Back":
        keyboard = [
            ["🤖 AI Chat", "🖼️ Image Generator"],
            ["🌐 Translator", "📁 Downloader"],
            ["⚙️ Settings", "ℹ️ Help"],
        ]

        await update.message.reply_text(
            "🏠 Main Menu",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            ),
        )
        return

    if user_text == "ℹ️ Help":
        await update.message.reply_text(
            "🤖 AI Chat\n"
            "🖼️ Image Generator\n"
            "🌐 Translator\n"
            "📁 Downloader\n"
            "⚙️ Settings"
        )
        return

    # ================= IMAGE GENERATOR =================

    if image_mode.get(user_id):
        image_mode[user_id] = False

        try:
            prompt = urllib.parse.quote(user_text)
            image_url = f"https://image.pollinations.ai/prompt/{prompt}"

            response = requests.get(image_url, timeout=120)

            if response.status_code != 200:
                await update.message.reply_text(
                    "❌ Failed to generate image."
                )
                return

            with open("image.png", "wb") as f:
                f.write(response.content)

            with open("image.png", "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption="✅ Image Generated Successfully!"
                )

            os.remove("image.png")

        except Exception as e:
            await update.message.reply_text(
                f"❌ Image Error:\n{e}"
            )

        return

    # ================= TRANSLATOR =================

    if translator_mode.get(user_id):
        translator_mode[user_id] = False

        try:
            translated = GoogleTranslator(
                source="auto",
                target="en"
            ).translate(user_text)

            await update.message.reply_text(
                f"🌍 Translation:\n\n{translated}"
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Translation Error:\n{e}"
            )

        return

    # ================= DOWNLOADER =================

    if downloader_mode.get(user_id):
        downloader_mode[user_id] = False

        try:
            await update.message.reply_text(
                "📥 Downloading... Please wait..."
            )

            ydl_opts = {
                "format": "best",
                "outtmpl": "video.%(ext)s",
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(user_text, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, "rb") as video:
                await update.message.reply_video(
                    video=video,
                    caption="✅ Download Complete!"
                )

            os.remove(filename)

        except Exception as e:
            await update.message.reply_text(
                f"❌ Download Error:\n{e}"
            )

        return

    # ================= AI CHAT =================

    if user_id not in user_memory:
        user_memory[user_id] = [
            {
                "role": "system",
                "content": "You are Alone Vampire AI. You are friendly, helpful and professional."
            }
        ]

    user_memory[user_id].append(
        {
            "role": "user",
            "content": user_text,
        }
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=user_memory[user_id],
        )

        reply = response.choices[0].message.content

        user_memory[user_id].append(
            {
                "role": "assistant",
                "content": reply,
            }
        )

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Error:\n{e}"
        )

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("clear", clear))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

create_tables()
print("🤖 Alone Vampire AI is Running...")

app.run_polling()