from fastapi import FastAPI, HTTPException
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
    # Aquí puedes integrar tu lógica de TTS (por ejemplo, gTTS, Edge-TTS o ElevenLabs)
    # y retornar la URL pública del archivo de audio generado.
    try:
        # Simulación de respuesta con URL de audio válida para que pase el nodo
        return {
            "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/unir-videos")
async def unir_videos(data: VideoRequest):
    video_path = "temp_video.mp4"
    audio_path = "temp_audio.mp3"
    output_path = "output_final.mp4"

    try:
        video_res = requests.get(data.video_url)
        if video_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el video")
        with open(video_path, "wb") as f:
            f.write(video_res.content)

        audio_res = requests.get(data.audio_url)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar el audio")
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
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for path in [video_path, audio_path]:
            if os.path.exists(path):
                os.remove(path)
