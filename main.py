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
    # 1. Aquí irá tu lógica de FFmpeg y renderizado del video...
    
    # 2. Actualizamos el estado a completado en memoria
    estados_tareas[task_id] = "completed"
    
    # 3. Notificamos al webhook de n8n para que despierte el nodo Wait
    try:
        requests.post(datos.webhook_url, json={"status": "completed", "task_id": task_id})
    except Exception as e:
        print(f"Error al notificar a n8n: {e}")

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
