from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import requests # Alat baru untuk nelpon API lain

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
    return {"message": "Mesin Hybrid Rizal: TikTok (API) + FB (yt-dlp)"}

@app.post("/api/download")
def download_video(request: VideoRequest):
    url = request.url

    # --- JALUR 1: KHUSUS TIKTOK & DOUYIN (Pakai TikWM API) ---
    if "tiktok.com" in url or "douyin.com" in url:
        try:
            # Kita minta tolong ke TikWM (Gratis & Stabil)
            response = requests.post(
                "https://www.tikwm.com/api/", 
                data={"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1}
            )
            data = response.json()

            if data.get("code") == 0:
                video_data = data.get("data", {})
                return {
                    "status": "success",
                    "title": video_data.get("title", "Video TikTok"),
                    "thumbnail": video_data.get("cover", ""),
                    # Prioritaskan link HD, kalau gak ada pakai link biasa
                    "download_url": video_data.get("play", "")
                }
            else:
                return {"status": "error", "message": "Video TikTok tidak ditemukan / Private."}
        
        except Exception as e:
            return {"status": "error", "message": f"Gagal jalur TikTok: {str(e)}"}

    # --- JALUR 2: SELAIN TIKTOK (Facebook, IG, dll) Pakai yt-dlp ---
    else:
        try:
            ydl_opts = {
                'format': 'best',
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "status": "success",
                    "title": info.get('title', 'Video'),
                    "thumbnail": info.get('thumbnail', ''),
                    "download_url": info.get('url', '')
                }

        except Exception as e:
            return {"status": "error", "message": "Gagal mengambil video (yt-dlp)."}