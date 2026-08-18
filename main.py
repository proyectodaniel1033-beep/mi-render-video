from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import requests
import os

app = FastAPI()


class VideoRequest(BaseModel):
    video_url: str
    audio_url: str


@app.post("/unir-videos")
async def unir_videos(data: VideoRequest):
    video_path = "temp_video.mp4"
    audio_path = "temp_audio.mp3"
    output_path = "output_final.mp4"

    try:
        # 1. Descargar video de Cloudinary
        video_res = requests.get(data.video_url)
        if video_res.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el video de Cloudinary")
        with open(video_path, "wb") as f:
            f.write(video_res.content)

        # 2. Descargar audio desde su URL
        audio_res = requests.get(data.audio_url)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el audio")
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # 3. Ejecutar FFmpeg para fusionar video y audio
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {result.stderr}")

        # Opcional: Aquí puedes subir `output_path` a Cloudinary de nuevo para devolver una URL pública del video final.
        
        return {
            "status": "success", 
            "message": "Video generado y unido correctamente"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Limpieza de archivos temporales en el contenedor para liberar memoria
        for path in [video_path, audio_path]:
            if os.path.exists(path):
                os.remove(path)
