import os
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class VideoRequest(BaseModel):
    audio_url: str
    videos: List[str]

@app.post("/transcode")
def transcode_video(data: VideoRequest):
    try:
        os.makedirs("/tmp/media", exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.6; Win64; x64)'}
        
        # 1. Descargar el audio de Catbox (Define la duración exacta del video final, ej. 2 min)
        audio_res = requests.get(data.audio_url, headers=headers)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el audio de Catbox.")
        
        audio_path = "/tmp/media/audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # 2. Descargar los videos de Pexels
        video_files = []
        for i, v_url in enumerate(data.videos):
            v_res = requests.get(v_url, headers=headers)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    f.write(v_res.content)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No hay videos válidos de Pexels.")

        # 3. Crear archivo concat para FFmpeg asegurando bucle si faltan segundos
        concat_list_path = "/tmp/media/concat_list.txt"
        with open(concat_list_path, "w") as f:
            # Si necesitas que se repitan los videos para alcanzar los 2+ minutos si la lista es corta:
            for _ in range(3): # Repite el set de clips varias veces por seguridad de duración
                for v_path in video_files:
                    f.write(f"file '{v_path}'\n")

        output_path = "/tmp/media/output_final.mp4"
        
        # 4. Comando FFmpeg: Corta exactamente a la duración del audio con '-shortest'
        command = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",  # Esto hace que el video dure exactamente lo que mide tu audio de Catbox (2 minutos o más)
            output_path
        ]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error FFmpeg: {result.stderr}")

        return {"message": "Video generado correctamente", "output": output_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
