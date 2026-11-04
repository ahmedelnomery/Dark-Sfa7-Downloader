import os
import re
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import yt_dlp

# 1. Web Server Keep-Alive /health
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask, daemon=True).start()

# 2. Telegram Bot Setup
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = Client("DarkSfa7Bot", api_id=6, api_hash="eb06630f012e11b0f73014e75139d300", bot_token=BOT_TOKEN)

# Custom yt-dlp Options to bypass blocks
YTDL_BASE_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "⚡ أهلاً بك في بوت **𝐃𝐚𝐫𝐤 𝐒𝐟𝐚𝟕 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐫**\n\n"
        "أرسل لي أي رابط من (تيك توك، إنستجرام، يوتيوب، ساوند كلاود، سبوتيفاي) وسأقوم بتحميله فوراً بأعلى جودة! 🎬🎵"
    )

@bot.on_message(filters.text & filters.private)
async def handle_link(client, message):
    url = message.text.strip()
    if not url.startswith("http"):
        return

    msg = await message.reply_text("🔎 جاري فحص الرابط واستخراج الوسائط...")

    try:
        ydl_opts = {**YTDL_BASE_OPTS, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Check if Photo Carousel / Slides
        if info.get('_type') == 'playlist' or info.get('entries'):
            entries = info.get('entries', [])
            images = [e.get('url') for e in entries if e.get('url')]
            
            if images:
                await msg.edit_text("📸 جاري تنزيل ألبوم الصور...")
                media_group = [InputMediaPhoto(img) for img in images[:10]]
                await message.reply_media_group(media_group)
                
                # Check for audio
                audio_url = info.get('audio_url') or info.get('url')
                if audio_url and not audio_url.endswith(('.jpg', '.png', '.jpeg')):
                    try:
                        await message.reply_audio(audio_url, caption="🎵 الصوت المرفق")
                    except Exception:
                        await message.reply_text("⚠️ تم تنزيل الصور بأعلى جودة، مسار الصوت غير متاح لهذا المنشور.")
                await msg.delete()
                return

        # Show Options for standard Video Links
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📹 تحميل فيديو بأعلى جودة", callback_data=f"vid|{url}")],
            [InlineKeyboardButton("🎵 تحميل صوت فقط بأعلى جودة", callback_data=f"aud|{url}")],
            [InlineKeyboardButton("🎬 تحميل فيديو وصوت معاً بأعلى جودة", callback_data=f"vid|{url}")]
        ])
        await msg.edit_text("إليك خيارات التحميل المتاحة للمنشور:", reply_markup=buttons)

    except Exception as e:
        await msg.edit_text("❌ عذراً، لم أستطع تنزيل الملف أو أن حجمه يتخطى الحجم المسموح به.")

@bot.on_callback_query(filters.regex(r"^(vid|aud)\|"))
async def process_download(client, callback_query):
    action, url = callback_query.data.split("|", 1)
    await callback_query.message.edit_text("⏳ جاري التحميل والمعالجة بأعلى جودة...")

    try:
        out_path = "downloads/%(id)s.%(ext)s"
        if action == "aud":
            opts = {**YTDL_BASE_OPTS, 'format': 'bestaudio/best', 'outtmpl': out_path}
        else:
            opts = {**YTDL_BASE_OPTS, 'format': 'bestvideo+bestaudio/best', 'outtmpl': out_path}

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if action == "aud":
            await callback_query.message.reply_audio(
                audio=filename,
                title=info.get('title', 'Dark Sfa7 Audio'),
                performer=info.get('uploader', 'Dark Sfa7')
            )
        else:
            await callback_query.message.reply_video(video=filename)

        await callback_query.message.delete()
        if os.path.exists(filename):
            os.remove(filename)

    except Exception:
        await callback_query.message.edit_text("عذراً، لم أستطع تنزيل الفيديو لتخطيه الحجم المسموح به.")

print("Bot started successfully...")
bot.run()
