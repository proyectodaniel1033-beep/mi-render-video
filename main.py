from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess
import requests
import os

app = FastAPI()

class VideoRequest(BaseModel):
    video_url: str
    audio_url: str

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/generar-voz")
async def generar_voz(data: VoiceRequest):
    try:
        # Endpoint simulado o integrado para la voz que devuelve una URL de audio válida
        return {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unir-videos")
async def unir_videos(request: Request):
    # Capturamos la petición en bruto para depurar si fuera necesario
    try:
        body = await request.json()
        print(f"DATOS RECIBIDOS EN RENDER: {body}")
        
        video_url = body.get("video_url")
        audio_url = body.get("audio_url")

        if not video_url or not audio_url:
            raise HTTPException(status_code=422, detail="Faltan las URL de video o audio")

        video_path = "temp_video.mp4"
        audio_path = "temp_audio.mp3"
        output_path = "output_final.mp4"

        # Descargar video
        video_res = requests.get(video_url)
        if video_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el video fuente")
        with open(video_path, "wb") as f:
            f.write(video_res.content)

        # Descargar audio
        audio_res = requests.get(audio_url)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el audio fuente")
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # Comando FFmpeg para fusionar
        cmd = [
            "ffmpeg", "-y",
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

        return {"status": "success", "message": "Video unido correctamente"}

    except Exception as e:
        print(f"ERROR INTERNO: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Limpieza de archivos temporales
        for path in ["temp_video.mp4", "temp_audio.mp3", "output_final.mp4"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
