import os
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class VideoRequest(BaseModel):
    audio_url: Optional[str] = None
    videos: Optional[List[str]] = None

@app.post("/transcode")
async def transcode_video(data: VideoRequest):
    print("--- JSON RECIBIDO DE N8N ---")
    print(data.dict())
    print("----------------------------")

    if not data.audio_url:
        raise HTTPException(status_code=422, detail="Falta el audio requerido.")

    os.makedirs("/tmp/media", exist_ok=True)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # 1. Descargar audio de GitHub
    audio_path = "/tmp/media/audio.mp3"
    try:
        audio_res = requests.get(data.audio_url, headers=headers, timeout=30)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar audio de GitHub")
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Fallo en descarga de audio.")

    # 2. Descarga optimizada (Limitada a máximo 6 clips para no saturar la RAM de Render)
    urls_a_probar = data.videos[:6] if data.videos else []
    fallback_video = "https://www.w3schools.com/html/mov_bbb.mp4"
    
    video_files = []
    
    for i, v_url in enumerate(urls_a_probar):
        try:
            print(f"Descargando clip {i}: {v_url}")
            v_res = requests.get(v_url, headers=headers, timeout=10, stream=True)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                video_files.append(v_path)
        except Exception:
            continue

    if not video_files:
        print("Usando video de respaldo...")
        try:
            v_res = requests.get(fallback_video, headers=headers, timeout=15, stream=True)
            if v_res.status_code == 200:
                v_path = "/tmp/media/fallback_video.mp4"
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)
                video_files.append(v_path)
        except Exception:
            pass

    if not video_files:
        raise HTTPException(status_code=400, detail="No se pudo procesar ningún clip de video.")

    # --- BUCLE EFICIENTE PARA LOS 2 MINUTOS SIN SATURAR ---
    original_videos = video_files.copy()
    while len(video_files) < 10 and len(original_videos) > 0:
        for v in original_videos:
            if len(video_files) >= 10:
                break
            video_files.append(v)
    # -----------------------------------------------------

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
        "-c:v", "libx264", "-preset", "ultrafast",  # Preset ultrarrápido para evitar timeout en Render
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-pix_fmt", "yuv420p",
        output_path
    ]
    
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        print(f"FFMPEG ERROR: {result.stderr}")
        raise HTTPException(status_code=500, detail="Error en FFmpeg.")

    return FileResponse(output_path, media_type="video/mp4", filename="conejo_millonario.mp4")
