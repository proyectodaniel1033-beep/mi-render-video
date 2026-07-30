import uuid
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Diccionario en memoria para almacenar el estado de las tareas
estados_tareas = {}

class TranscodeRequest(BaseModel):
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    webhook_url: Optional[str] = None

def procesar_video(task_id: str, datos: TranscodeRequest):
    try:
        # 1. Aquí puedes descargar los archivos usando datos.video_url y datos.audio_url
        # 2. Aquí ejecutas tu lógica de FFmpeg (por ejemplo, con subprocess)
        print(f"Procesando video para la tarea {task_id} con URL: {datos.video_url}")
        
        # Simulamos el proceso de renderizado...
        
        # 3. Actualizamos el estado a completado
        estados_tareas[task_id] = "completado"
        
        # 4. Notificamos al webhook de n8n para que despierte el nodo Wait
        if datos.webhook_url:
            requests.post(
                datos.webhook_url, 
                json={"status": "completado", "task_id": task_id}
            )
    except Exception as e:
        estados_tareas[task_id] = "error"
        print(f"Error en el proceso de video: {e}")

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
    return {"id": task_id, "status": estado}
