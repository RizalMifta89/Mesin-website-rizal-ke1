from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Mesin Rizal Versi TikTok-Killer Aktif!"}

@app.post("/api/download")
def download_video(request: VideoRequest):
    try:
        # --- KONFIGURASI BARU KHUSUS TIKTOK ---
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True, # Abaikan sertifikat SSL (kadang bikin error)
            'ignoreerrors': True,
            
            # INI TOPENGNYA: Kita menyamar sebagai Google Chrome di Windows
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            
            # Tambahan untuk ekstraksi TikTok agar lebih bandel
            'extractor_args': {
                'tiktok': {
                    'app_version': ['25.0.0'], # Pura-pura pakai aplikasi versi lama yg stabil
                    'tt_webid_v2': ['1234567890123456789'] # ID palsu
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Ekstrak info
            info = ydl.extract_info(request.url, download=False)
            
            # Validasi jika gagal mengambil info
            if not info:
                return {"status": "error", "message": "Gagal mengambil data video. Mungkin diprivate atau diblokir."}

            # Ambil data
            video_url = info.get('url', None)
            title = info.get('title', 'Video TikTok')
            thumbnail = info.get('thumbnail', '')
            
            # Fallback (Jaga-jaga) jika URL ada di tempat lain
            if not video_url:
                 # Kadang TikTok menaruh link di 'entries' kalau berupa playlist
                 if 'entries' in info:
                     video_url = info['entries'][0].get('url')

            return {
                "status": "success",
                "title": title,
                "download_url": video_url,
                "thumbnail": thumbnail
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}