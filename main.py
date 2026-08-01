import uuid
import requests
from fastapi import FastAPI, BackgroundTasks
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
        # ... Tu código de FFmpeg y procesamiento de video ...
        
        estados_tareas[task_id] = "completado"

        # Notificar a n8n de forma limpia y directa
        if datos.webhook_url:
            url_real = datos.webhook_url.replace("http://localhost:5678", "https://resend-patriot-dehydrate.ngrok-free.dev")
            response = requests.get(url_real)
            print(f"Webhook enviado a n8n: {response.status_code}")

    except Exception as e:
        estados_tareas[task_id] = "error"
        print(f"Error procesando video: {str(e)}")

@app.post("/transcode")
def iniciar_transcodificacion(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Guardamos el estado inicial
    estados_tareas[task_id] = "pendiente"
    
    # Ejecutar en segundo plano para que Render no corte la petición HTTP
    background_tasks.add_task(procesar_video, task_id, datos)
    
    return {"id": task_id, "status": "pending"}

@app.get("/")
def read_root():
    return {"mensaje": "¡Tu servicio está live!"}
