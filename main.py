import os
import subprocess
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class VideoRequest(BaseModel):
    audio_url: Optional[str] = None
    videos: Optional[List[str]] = None
    url: Optional[str] = None

@app.post("/transcode")
async def transcode_video(request: Request):
    # 1. Imprimir en los logs de Render lo que llegó exactamente desde n8n
    body_json = await request.json()
    print("--- JSON RECIBIDO DE N8N ---")
    print(body_json)
    print("----------------------------")
    
    try:
        data = VideoRequest(**body_json)
        final_audio_url = data.audio_url or data.url
        
        if not final_audio_url:
            raise HTTPException(status_code=422, detail="El JSON no contiene 'audio_url' ni 'url'.")
        
        if not data.videos or len(data.videos) == 0:
            raise HTTPException(status_code=422, detail="El JSON no contiene la lista de 'videos' o está vacía.")

        os.makedirs("/tmp/media", exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # Descargar audio
        audio_res = requests.get(final_audio_url, headers=headers)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar el audio. Código HTTP: {audio_res.status_code}")
        
        audio_path = "/tmp/media/audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_res.content)

        # Descargar videos
        video_files = []
        for i, v_url in enumerate(data.videos):
            v_res = requests.get(v_url, headers=headers)
            if v_res.status_code == 200:
                v_path = f"/tmp/media/video_{i}.mp4"
                with open(v_path, "wb") as f:
                    f.write(v_res.content)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de la lista proporcionada.")

        # Crear lista para FFmpeg
        concat_list_path = "/tmp/media/concat_list.txt"
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        # Procesar con FFmpeg
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
        print(f"Error interno: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
