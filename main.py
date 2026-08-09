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
    
    # 1. Descargar audio de GitHub (que ya sabemos que funciona)
    audio_path = "/tmp/media/audio.mp3"
    try:
        audio_headers = {'User-Agent': 'Mozilla/5.0'}
        audio_res = requests.get(data.audio_url, headers=audio_headers, timeout=30)
        print(f"DEBUG AUDIO: Status {audio_res.status_code}, Bytes: {len(audio_res.content)}")
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Error al descargar audio de GitHub")
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)
    except Exception as e:
        print(f"EXCEPCIÓN AUDIO: {str(e)}")
        raise HTTPException(status_code=400, detail="Fallo en descarga de audio.")

    # 2. Descargar clips de video de Pexels CON TU TOKEN DE API
    # REEMPLAZA 'TU_API_KEY_DE_PEXELS' por la misma clave que usas en el nodo Pexels de n8n
    PEXELS_API_KEY = "7MG2eewyLnfL5DSATmFDQJ144nSx40aIZlZ9KZCrnetbJAhd5jTM"

    video_headers = {
        'User-Agent': 'Mozilla/5.0',
        'Authorization': PEXELS_API_KEY
}

    video_files = []
    for i, v_url in enumerate(data.videos[:5]):
        try:
            print(f"Descargando video {i}: {v_url}")
            v_res = requests.get(v_url, headers=video_headers, timeout=25, stream=True)
            print(f"DEBUG VIDEO {i}: Status {v_res.status_code}")
            
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                video_files.append(v_path)
        except Exception as ex:
            print(f"Error descargando clip {i}: {str(ex)}")
            continue

    if not video_files:
        raise HTTPException(status_code=400, detail="No se pudieron descargar los clips de video de Pexels.")

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
        raise HTTPException(status_code=500, detail="Error en el procesamiento de video con FFmpeg.")

    return {"message": "Video generado con éxito", "url_archivo": "output_final.mp4"}
