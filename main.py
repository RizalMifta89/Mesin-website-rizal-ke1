import os
import logging
import telebot
import yt_dlp
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telebot import types

# --- KONFIGURASI ---
# Token diambil dari Environment Variable di Render
BOT_TOKEN = os.getenv("BOT_TOKEN") 
APP_URL = os.getenv("RENDER_EXTERNAL_URL") 

# Inisialisasi Bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

app = FastAPI()

# --- CORS (Agar API bisa diakses website lain jika perlu) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FUNGSI DOWNLOADER (High Quality - Tanpa Cookies) ---
def process_video_download(url):
    ydl_opts = {
        # 1. MEMAKSA KUALITAS TERBAIK (MP4)
        # Kita minta format mp4 terbaik yang ada video+audio nya.
        'format': 'best[ext=mp4]/best', 
        
        # 2. MENYAMAR JADI IPHONE (User Agent)
        # Agar server IG/TikTok mengira ini permintaan dari HP, bukan bot.
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        
        # 3. PENGATURAN UMUM
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak info video
            info = ydl.extract_info(url, download=False)
            
            # Ambil URL video streaming
            final_url = info.get('url', None)
            
            return {
                "status": "success",
                "title": info.get('title', 'Video Downloaded'),
                "url": final_url,
                "thumbnail": info.get('thumbnail', '')
            }

    except Exception as e:
        error_msg = str(e)
        print(f"Error Log: {error_msg}") # Print error ke log Render untuk debugging
        
        # Pesan error yang lebih manusiawi untuk user bot
        if "Sign in" in error_msg or "unavailable" in error_msg:
            return {"status": "error", "message": "Video tidak bisa diambil (Private/Konten Dewasa/Login Required)."}
        
        return {"status": "error", "message": "Gagal mengambil video. Pastikan link valid dan publik."}

# --- HANDLER BOT TELEGRAM ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Halo! Kirimkan link TikTok, Instagram, atau Facebook.\nSaya akan kirimkan videonya dengan kualitas terbaik (jika publik).")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # Validasi sederhana
    if not url.startswith(('http', 'www')):
        bot.reply_to(message, "❌ Link tidak valid. Pastikan link diawali http atau www.")
        return

    # Kirim notifikasi "Sedang mengetik/mengirim video..."
    bot.send_chat_action(message.chat.id, 'upload_video')
    msg_loading = bot.reply_to(message, "⏳ Sedang memproses video HD...")
    
    # Jalankan proses download
    result = process_video_download(url)

    if result['status'] == 'success':
        try:
            # Kirim Video
            bot.send_video(
                message.chat.id,
                result['url'],
                caption=f"🎥 **{result['title']}**",
                parse_mode="Markdown"
            )
            # Hapus pesan loading agar chat bersih
            bot.delete_message(message.chat.id, msg_loading.message_id)
            
        except Exception as e:
            # Kadang URL valid tapi file terlalu besar untuk Telegram atau expired cepat
            bot.edit_message_text(f"⚠️ Gagal mengirim video ke Telegram.\nError: {e}", message.chat.id, msg_loading.message_id)
    else:
        # Jika gagal download (misal private)
        bot.edit_message_text(f"❌ {result['message']}", message.chat.id, msg_loading.message_id)

# --- RUTE FASTAPI (WEBHOOK & API) ---

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Server Bot Telegram Aktif!"}

# Endpoint Webhook (Pintu masuk pesan Telegram)
@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    json_str = await request.json()
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK"

# Endpoint API (Opsional, jika kamu masih pakai untuk website)
@app.post("/api/download")
def download_video_api(request: VideoRequest):
    return process_video_download(request.url)

# --- SETTING WEBHOOK SAAT STARTUP ---
@app.on_event("startup")
def set_webhook():
    if BOT_TOKEN and APP_URL:
        webhook_url = f"{APP_URL}/webhook/{BOT_TOKEN}"
        # Hapus webhook lama dulu biar bersih
        bot.remove_webhook()
        # Set webhook baru
        bot.set_webhook(url=webhook_url)
        print(f"Webhook berhasil di-set ke: {webhook_url}")
    else:
        print("PERINGATAN: BOT_TOKEN atau RENDER_EXTERNAL_URL belum diset di Environment Variables.")