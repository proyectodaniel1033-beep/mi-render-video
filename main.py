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
        # ... Aquí va tu código de FFmpeg y procesamiento de video ...
        # Supongamos que tu video terminado queda guardado en una URL o ruta accesible:
        url_video_terminado = "https://cdn.pixabay.com/video/2016/02/29/2340-157269921_large.mp4"
        
        estados_tareas[task_id] = "completado"

        # Notificar a n8n de forma limpia y directa mediante POST
        if datos.webhook_url:
            url_real = datos.webhook_url.replace("http://localhost:5678", "https://tu-url-de-ngrok.ngrok-free.dev")
            
            payload = {
                "task_id": task_id,
                "status": "success",
                "video_result_url": url_video_terminado
            }
            
            # Usamos POST para enviar la información al Webhook de n8n
            response = requests.post(url_real, json=payload)
            print(f"Webhook enviado a n8n: {response.status_code}")

    except Exception as e:
        estados_tareas[task_id] = "error"
        print(f"Error procesando video: {str(e)}")

@app.post("/transcode")
def iniciar_transcodificacion(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Guardamos el estado inicial
    estados_tareas[task_id] = "pendientes"
    
    # Ejecutar en segundo plano para que Render no corte la petición
    background_tasks.add_task(procesar_video, task_id, datos)
    
    return {"id": task_id, "status": "pending"}

@app.get("/")
def read_root():
    return {"mensaje": "¡Tu servicio está live!"}
