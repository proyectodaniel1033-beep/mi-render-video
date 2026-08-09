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

@app.post("/transcode")
async def transcode_video(data: VideoRequest):
    print(f"--- JSON RECIBIDO DE N8N ---")
    print(data.dict())
    print(f"----------------------------")

    if not data.audio_url or not data.videos:
        raise HTTPException(status_code=422, detail="Faltan datos requeridos.")

    os.makedirs("/tmp/media", exist_ok=True)
    
    # Headers completos para engañar a GitHub y permitir la descarga del MP3
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
    }
    
    # 1. Descargar audio de GitHub con manejo de errores detallado
    audio_path = "/tmp/media/audio.mp3"
    try:
        audio_res = requests.get(data.audio_url, headers=headers, timeout=30)
        print(f"DEBUG AUDIO: Status {audio_res.status_code}, Bytes: {len(audio_res.content)}")
        
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"GitHub respondió con error HTTP {audio_res.status_code}")
            
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)
            
    except Exception as e:
        print(f"EXCEPCIÓN AUDIO: {str(e)}")
        raise HTTPException(status_code=400, detail="No se pudo conectar con el enlace de GitHub.")

    # 2. Descargar clips de video de Pexels
    video_files = []
    for i, v_url in enumerate(data.videos[:5]):
        try:
            v_res = requests.get(v_url, headers=headers, timeout=15)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    f.write(v_res.content)
                video_files.append(v_path)
        except Exception:
            continue

    if not video_files:
        raise HTTPException(status_code=400, detail="No se pudieron descargar los clips de video.")

    # 3. Crear lista para FFmpeg
    concat_list_path = "/tmp/media/concat_list.txt"
    with open(concat_list_path, "w") as f:
        for v_path in video_files:
            f.write(f"file '{v_path}'\n")

    # 4. Procesar con FFmpeg
    output_path = "/tmp/media/output_final.mp4"
    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-pix_fmt", "yuv420p",
        output_path
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"FFMPEG ERROR: {result.stderr}")
        raise HTTPException(status_code=500, detail="Error en el procesamiento de video.")

    return {"message": "Video generado con éxito", "url_archivo": "output_final.mp4"}
