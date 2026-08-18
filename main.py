from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import subprocess
import requests
import os

app = FastAPI()

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/generar-voz")
async def generar_voz(data: VoiceRequest):
    try:
        return {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unir-videos")
async def unir_videos(request: Request):
    try:
        body = await request.json()
        print(f"DATOS RECIBIDOS EN RENDER: {body}")
        
        # Extraer video_url soportando si viene directo o anidado en 'urls'
        video_url = None
        if "video_url" in body:
            video_url = body.get("video_url")
        elif "urls" in body:
            urls_data = body.get("urls")
            if isinstance(urls_data, dict) and "urls" in urls_data:
                video_url = urls_data["urls"][0] if urls_data["urls"] else None
            elif isinstance(urls_data, list):
                video_url = urls_data[0] if urls_data else None

        # Extraer audio_url
        audio_url = body.get("audio_url")

        if not video_url or not audio_url:
            raise HTTPException(status_code=422, detail=f"Faltan las URL. Recibido video: {video_url}, audio: {audio_url}")

        video_path = "temp_video.mp4"
        audio_path = "temp_audio.mp3"
        output_path = "output_final.mp4"

        video_res = requests.get(video_url)
        if video_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el video fuente")
        with open(video_path, "wb") as f:
            f.write(video_res.content)

        audio_res = requests.get(audio_url)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el audio fuente")
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

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
        for path in ["temp_video.mp4", "temp_audio.mp3", "output_final.mp4"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
