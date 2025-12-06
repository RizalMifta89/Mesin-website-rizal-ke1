import os
import logging
import telebot
import yt_dlp
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telebot import types

# --- KONFIGURASI ---
# Ambil Token dari Environment Variable (Setting di Render nanti)
BOT_TOKEN = os.getenv("BOT_TOKEN") 
# Render otomatis menyediakan URL aplikasi kamu di env var ini
APP_URL = os.getenv("RENDER_EXTERNAL_URL") 

# Inisialisasi Bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNGSI DOWNLOADER (Dipakai oleh API & Bot) ---
def process_video_download(url):
    ydl_opts = {
        'format': 'best', 
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "success",
                "title": info.get('title', 'Video Downloaded'),
                "url": info.get('url', None),
                "thumbnail": info.get('thumbnail', '')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- LOGIKA BOT TELEGRAM ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Kirim link IG/FB/TikTok, saya akan ambilkan videonya.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if not url.startswith(('http', 'www')):
        bot.reply_to(message, "Link tidak valid.")
        return

    msg = bot.reply_to(message, "⏳ Mencari video...")
    
    # Panggil fungsi downloader yang sama dengan API
    result = process_video_download(url)

    if result['status'] == 'success':
        try:
            bot.send_video(
                message.chat.id,
                result['url'],
                caption=f"🎥 **{result['title']}**",
                parse_mode="Markdown"
            )
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"Gagal kirim: {e}", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text(f"Gagal download: {result['message']}", message.chat.id, msg.message_id)

# --- RUTE FASTAPI ---

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Server Bot & API Aktif!"}

# Endpoint Webhook untuk Telegram (Rahasia)
@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    # Terima update dari Telegram
    json_str = await request.json()
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK"

# Endpoint API Download (Yang kamu minta sebelumnya)
@app.post("/api/download")
def download_video_api(request: VideoRequest):
    return process_video_download(request.url)

# --- SET WEBHOOK SAAT STARTUP ---
# Ini penting agar Telegram tahu harus kirim pesan ke mana
@app.on_event("startup")
def set_webhook():
    if BOT_TOKEN and APP_URL:
        webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
        print(f"Setting webhook to: {webhook_url}")
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
    else:
        print("BOT_TOKEN atau RENDER_EXTERNAL_URL belum diset.")