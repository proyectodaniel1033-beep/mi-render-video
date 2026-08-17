import os
import subprocess
import tempfile
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests

app = FastAPI()

class VideoPayload(BaseModel):
    urls: List[str]

@app.post("/unir-videos")
def unir_videos(payload: VideoPayload):
    try:
        if not payload.urls:
            raise HTTPException(status_code=400, detail="La lista de URLs está vacía.")
        
        # Creamos un directorio temporal para trabajar limpios en Render
        with tempfile.TemporaryDirectory() as tmpdirname:
            lista_txt_path = os.path.join(tmpdirname, "lista.txt")
            video_paths = []

            # 1. Descargar cada video de la lista
            for idx, url in enumerate(payload.urls):
                response = requests.get(url, stream=True, timeout=15)
                if response.status_code == 200:
                    video_path = os.path.join(tmpdirname, f"video_{idx}.mp4")
                    with open(video_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    video_paths.append(video_path)
                else:
                    print(f"Error descargando URL {url}, código: {response.status_code}")

            if not video_paths:
                raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de las URLs proporcionadas.")

            # 2. Crear el archivo de texto para FFmpeg
            with open(lista_txt_path, "w") as f:
                for path in video_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")

            output_video_path = os.path.join(tmpdirname, "salida_final.mp4")

            # 3. Comando de FFmpeg
            comando = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", lista_txt_path,
                "-t", "120", 
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-crf", "23",
                "-preset", "fast",
                "-c:a", "aac",
                output_video_path
            ]

            resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if resultado.returncode != 0:
                print(f"Error interno de FFmpeg: {resultado.stderr}")
                raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {resultado.stderr}")

            return {
                "status": "success",
                "message": "¡Videos unidos correctamente!",
                "total_videos_procesados": len(video_paths)
            }

    except Exception as e:
        print(f"Excepción capturada: str(e)")
        raise HTTPException(status_code=500, detail=str(e))
