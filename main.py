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
    # --- DEPURACIÓN: Esto imprimirá exactamente qué recibe Render en los logs ---
    print(f"--- JSON RECIBIDO DE N8N ---")
    print(data.dict())
    print(f"----------------------------")
    # ----------------------------------------------------------------------------

    # Validar datos básicos
    if not data.audio_url or not data.videos:
        raise HTTPException(status_code=422, detail="Faltan datos requeridos.")
    
    # ... resto de tu código ....")

    os.makedirs("/tmp/media", exist_ok=True)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # 1. Descargar audio con validación
    audio_path = "/tmp/media/audio.mp3"
    audio_res = requests.get(data.audio_url, headers=headers, timeout=20)
    if audio_res.status_code != 200 or len(audio_res.content) < 500:
        raise HTTPException(status_code=400, detail="El audio de Catbox no se descargó correctamente.")
    
    with open(audio_path, "wb") as f:
        f.write(audio_res.content)

    # 2. Descargar clips de video
    video_files = []
    for i, v_url in enumerate(data.videos[:5]): # Limitamos a 5 clips
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

    # 4. Procesar con FFmpeg (ajustado para mayor compatibilidad)
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
        # Imprimir error real en logs de Render para depurar
        print(f"FFMPEG ERROR: {result.stderr}")
        raise HTTPException(status_code=500, detail="Error en el procesamiento de video.")

    return {"message": "Video generado con éxito", "url_archivo": "output_final.mp4"}
