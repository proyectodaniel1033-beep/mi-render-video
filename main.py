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
    if not payload.urls:
        raise HTTPException(status_code=400, detail="No se recibieron URLs de video.")
    
    # Creamos un directorio temporal para trabajar limpios en Render
    with tempfile.TemporaryDirectory() as tmpdirname:
        lista_txt_path = os.path.join(tmpdirname, "lista.txt")
        video_paths = []

        try:
            # 1. Descargar cada video de la lista de Pexels
            for idx, url in enumerate(payload.urls):
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    video_path = os.path.join(tmpdirname, f"video_{idx}.mp4")
                    with open(video_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    video_paths.append(video_path)
                else:
                    raise HTTPException(status_code=400, detail=f"No se pudo descargar el video de la URL: {url}")

            # 2. Crear el archivo de texto que FFmpeg necesita para concatenar
            with open(lista_txt_path, "w") as f:
                for path in video_paths:
                    # Usamos rutas absolutas seguras para FFmpeg
                    f.write(f"file '{os.path.abspath(path)}'\n")

            output_video_path = os.path.join(tmpdirname, "salida_final.mp4")

            # 3. Comando de FFmpeg para unir y ajustar a 120 segundos (2 minutos)
            # -t 120 corta o fuerza la duración exacta a 2 minutos
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

            # Ejecutar FFmpeg en el sistema operativo de Render
            resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if resultado.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {resultado.stderr}")

            # Nota: Aquí puedes agregar código extra para subir tu 'output_video_path' 
            # a Cloudinary, Google Drive o regresarlo como respuesta.
            
            return {
                "status": "success",
                "message": "¡Videos unidos y procesados correctamente con FFmpeg!",
                "duracion_objetivo": "120 segundos"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str.startswith(str(e)))
