import os
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class VideoRequest(BaseModel):
    audio_url: Optional[str] = None
    videos: Optional[List[str]] = None
    # Por si n8n manda las variables con otro nombre secundario
    url: Optional[str] = None 

@app.post("/transcode")
def transcode_video(data: VideoRequest):
    try:
        # Aceptar audio_url o url genérica
        final_audio_url = data.audio_url or data.url
        if not final_audio_url:
            raise HTTPException(status_code=422, detail="Falta la URL del audio en la petición.")
        
        if not data.videos or len(data.videos) == 0:
            raise HTTPException(status_code=422, detail="La lista de videos está vacía.")

        os.makedirs("/tmp/media", exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # 1. Descargar audio
        audio_res = requests.get(final_audio_url, headers=headers)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el audio.")
        
        audio_path = "/tmp/media/audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # 2. Descargar videos
        video_files = []
        for i, v_url in enumerate(data.videos):
            v_res = requests.get(v_url, headers=headers)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    f.write(v_res.content)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video.")

        # 3. Crear lista para FFmpeg
        concat_list_path = "/tmp/media/concat_list.txt"
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        # 4. Procesar video final
        output_path = "/tmp/media/output_final.mp4"
        command = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error FFmpeg: {result.stderr}")

        return {"message": "¡Video generado con éxito!", "output": output_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
