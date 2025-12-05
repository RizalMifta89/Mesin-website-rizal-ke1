from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

# --- PENTING: PENGATURAN IZIN AKSES (CORS) ---
# Ini agar website Vercel Anda boleh mengakses mesin ini.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tanda bintang artinya semua boleh akses (untuk belajar)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Mesin SnapDouyin Aktif! Siap menerima perintah."}

@app.post("/api/download")
def download_video(request: VideoRequest):
    try:
        # Konfigurasi yt-dlp untuk mengambil link langsung
        ydl_opts = {
            'format': 'best', # Ambil kualitas terbaik
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak informasi video tanpa mendownload filenya ke server
            info = ydl.extract_info(request.url, download=False)
            
            # Ambil data yang dibutuhkan
            video_url = info.get('url', None)
            title = info.get('title', 'Video TikTok')
            thumbnail = info.get('thumbnail', '')
            
            return {
                "status": "success",
                "title": title,
                "download_url": video_url,
                "thumbnail": thumbnail
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}