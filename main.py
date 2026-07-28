import os
import uuid
import subprocess
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

# Diccionario global para guardar el estado de las tareas
estados_tareas = {}

class TranscodeRequest(BaseModel):
    image_url: str
    audio_url: str

def procesar_video(task_id: str, image_url: str, audio_url: str):
    try:
        estados_tareas[task_id] = "pending"
        
        ruta_imagen = f"imagen_{task_id}.jpg"
        ruta_audio = f"audio_{task_id}.mp3"
        ruta_archivo = f"video_{task_id}.mp4"
        
        # 1. Descargar la imagen
        img_data = requests.get(image_url).content
        with open(ruta_imagen, "wb") as handler:
            handler.write(img_data)
            
        # 2. Descargar el audio
        audio_data = requests.get(audio_url).content
        with open(ruta_audio, "wb") as handler:
            handler.write(audio_data)
            
        # 3. Comando FFmpeg para unificar imagen y audio
        comando = [
            "ffmpeg",
            "-loop", "1",
            "-i", ruta_imagen,
            "-i", ruta_audio,
            "-t", "120",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            ruta_archivo
        ]
        
        subprocess.run(comando, check=True)
        estados_tareas[task_id] = "completed"
        
    except Exception as e:
        print(f"Error en el proceso: {e}")
        estados_tareas[task_id] = "error"
    finally:
        # Limpiar archivos temporales locales
        for ruta in [ruta_imagen, ruta_audio]:
            if os.path.exists(ruta):
                os.remove(ruta)

@app.post("/transcode")
def iniciar_transcode(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    
    # Ejecutar en segundo plano para que Render no corte la petición HTTP
    background_tasks.add_task(procesar_video, task_id, datos.image_url, datos.audio_url)
    
    return {"id": task_id, "estado": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    if task_id not in estados_tareas:
        return {"estado": "no_encontrado"}
    return {"estado": estados_tareas[task_id]}
