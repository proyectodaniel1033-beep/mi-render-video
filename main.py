import os
import uuid
import subprocess
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Diccionario en memoria para almacenar el estado de las tareas
estados_tareas = {}

class TranscodeRequest(BaseModel):
    video_url: str
    audio_url: str
    webhook_url: str

def procesar_video(task_id: str, datos: TranscodeRequest):
    # Aquí irá tu lógica de transcodificación con FFmpeg
    pass

@app.post("/transcode")
def iniciar_transcodificacion(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Guardamos el estado inicial
    estados_tareas[task_id] = "pendiente"
    
    # Ejecutar en segundo plano para que Render no corte la petición HTTP
    background_tasks.add_task(procesar_video, task_id, datos)
    
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    estado = estados_tareas.get(task_id, "no_encontrado")
    return {"id": task_id, "status": status}
