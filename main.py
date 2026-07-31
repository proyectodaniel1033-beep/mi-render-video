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
    # ... todo tu código de FFmpeg y proceso de video va aquí ...
    
    estados_tareas[task_id] = "completado"

    # Notificar a n8n cuando finalice con éxito
    
    
if datos.webhook_url:
        url_real = datos.webhook_url.replace("http://localhost:5678", "https://resend-patriot-dehydrate.ngrok-free.dev")
        response = requests.get(url_real)
        print(f"Webhook enviado a n8n: {response.status_code}")

except Exception as e:
    # Este bloque es obligatorio para que el try no de SyntaxError
    estados_tareas[task_id] = "error"
    print(f"Error en la tarea: {str(e)}")

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
