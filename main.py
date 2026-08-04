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
        
        # 1. Cabecera para evitar que Catbox rechace la descarga por seguridad
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # 2. Descargar audio de Catbox
        audio_res = requests.get(data.audio_url, headers=headers)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="No se pudo descargar el audio de Catbox.")
        
        audio_path = "/tmp/media/audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # 3. Descargar videos de Pexels uno por uno
        video_files = []
        for i, v_url in enumerate(data.videos):
            v_res = requests.get(v_url, headers=headers)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    f.write(v_res.content)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de Pexels.")

        # 4. Crear archivo de lista para FFmpeg
        concat_list_path = "/tmp/media/concat_list.txt"
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        # 5. Ejecutar FFmpeg para unir videos y recortar al tamaño del audio (~2 min)
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
