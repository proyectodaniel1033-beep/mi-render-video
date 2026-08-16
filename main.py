import os
import subprocess
import tempfile
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any

app = FastAPI()

class VideoPayload(BaseModel):
    urls: Any # Aceptamos cualquier formato para mayor compatibilidad con n8n

@app.post("/unir-videos")
def unir_videos(payload: VideoPayload):
    # Lógica robusta para extraer la lista de URLs
    data = payload.urls
    lista_urls = []
    
    if isinstance(data, list):
        lista_urls = data
    elif isinstance(data, dict):
        # Si n8n envía un objeto, buscamos valores que parezcan URLs
        lista_urls = [v for v in data.values() if isinstance(v, str) and v.startswith("http")]
    
    if not lista_urls:
        raise HTTPException(status_code=400, detail="No se encontraron URLs válidas en el cuerpo de la petición.")

    with tempfile.TemporaryDirectory() as tmpdirname:
        lista_txt_path = os.path.join(tmpdirname, "lista.txt")
        video_paths = []

        try:
            # Descarga
            for idx, url in enumerate(lista_urls):
                resp = requests.get(url, stream=True, timeout=15)
                if resp.status_code == 200:
                    v_path = os.path.join(tmpdirname, f"v_{idx}.mp4")
                    with open(v_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=1024*1024):
                            f.write(chunk)
                    video_paths.append(v_path)

            # Preparación para FFmpeg
            with open(lista_txt_path, "w") as f:
                for path in video_paths:
                    f.write(f"file '{path}'\n")

            salida = os.path.join(tmpdirname, "final.mp4")
            
            # FFmpeg: Unir y convertir
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt_path,
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast", "-c:a", "aac", salida
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)

            return {"status": "success", "message": "Video procesado correctamente"}

        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {e.stderr.decode()}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
