import yt_dlp
import os
import sqlite3
import requests
import asyncio
import uuid

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8756922348:AAEpHpft5w1oYMjdvhLxHDuyhW6js_gZh-c"
ADMIN_ID = 6819184797

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
username TEXT,
country TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS downloads(
user_id INTEGER,
link TEXT
)
""")

conn.commit()

# ================= DETEKSI NEGARA =================

def get_country():

    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        data = r.json()
        return data.get("country_name","Unknown")

    except:
        return "Unknown"

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    country = get_country()

    cursor.execute(
        "INSERT OR IGNORE INTO users VALUES (?,?,?)",
        (user.id, user.username, country)
    )

    conn.commit()

    text = f"""
👋 Halo {user.first_name}

🚀 Downloader Bot

🎬 Support:
• TikTok
• YouTube
• Instagram

📌 Cara pakai:
Kirim link video untuk download

━━━━━━━━━━━━━━
👨‍💻 Developer : ilal
"""

    await update.message.reply_text(text)

# ================= DOWNLOAD =================

def download_video(url):

    filename = f"{uuid.uuid4()}.mp4"

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": filename,
        "merge_output_format": "mp4",
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return filename

# ================= HANDLE LINK =================

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = update.message.text
    user = update.effective_user

    if "http" not in url:

        await update.message.reply_text("❌ Kirim link yang valid")
        return

    await update.message.reply_text("⚡ Sedang memproses...")

    cursor.execute(
        "INSERT INTO downloads VALUES (?,?)",
        (user.id, url)
    )

    conn.commit()

    loop = asyncio.get_running_loop()

    try:

        filename = await loop.run_in_executor(None, download_video, url)

        with open(filename, "rb") as video:

            await update.message.reply_video(video)

        os.remove(filename)

    except:

        await update.message.reply_text("❌ Gagal download video")

# ================= ADMIN PANEL =================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text("❌ Kamu bukan admin")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM downloads")
    downloads = cursor.fetchone()[0]

    text = f"""
👑 ADMIN PANEL

👥 Total User : {users}
📥 Total Download : {downloads}

━━━━━━━━━━━━━━
Developer : ilal
"""

    await update.message.reply_text(text)

# ================= USER LIST =================

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM users")

    data = cursor.fetchall()

    text = "👥 LIST USER\n\n"

    for u in data:

        text += f"""
ID : {u[0]}
Username : {u[1]}
Negara : {u[2]}

"""

    await update.message.reply_text(text)

# ================= RUN BOT =================

app = ApplicationBuilder().token(BOT_TOKEN).concurrent_updates(True).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("users", users))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("🚀 BOT ONLINE")
app.run_polling()