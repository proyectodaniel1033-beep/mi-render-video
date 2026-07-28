import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Diccionario en memoria para almacenar el estado de las tareas
estados_tareas = {}

import subprocess

def proceso_ffmpeg_real(task_id: str):
    ruta_archivo = f"video_procesado_{task_id}.mp4"
    comando = [
        "ffmpeg",
        "-loop", "1",
        "-i", "imagen_fondo.jpg",  # Tu imagen de fondo
        "-i", "audio_voz.mp3",       # Tu archivo de audio o voz generada
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",                 # Termina el video cuando acabe el audio
        ruta_archivo
    ]
    try:
        subprocess.run(comando, check=True)
        estados_tareas[task_id] = "completed"
    except Exception as e:
        estados_tareas[task_id] = "error"

@app.post("/transcode")
def crear_trabajo(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    background_tasks.add_task(proceso_ffmpeg_real, task_id)
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    # Devuelve la clave 'status' exactamente como la espera el nodo If en n8n
    return {"id": task_id, "status": estados_tareas[task_id]}

@app.get("/download/{task_id}")
def descargar_video(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    ruta_archivo = f"video_procesado_{task_id}.mp4"
    
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo de video no encontrado")
    
    return FileResponse(ruta_archivo, media_type="video/mp4", filename="video_final.mp4")
