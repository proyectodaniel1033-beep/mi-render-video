import uuid
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
estados_tareas = {}

class TranscodeRequest(BaseModel):
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    webhook_url: Optional[str] = None

def procesar_video(task_id: str, datos: TranscodeRequest):
    try:
        url_video_terminado = "https://cdn.pixabay.com/video/2016/02/29/2340-157269921_large.mp4"
        estados_tareas[task_id] = "completado"

        # Usa tu URL de prueba de n8n aquí directamente entre las comillas
        url_real = "https://resend-patriot-dehydrate.ngrok-free.dev/webhook-test/97ce5368-1272-468e-85c3-fdaf840605fb"
        
        payload = {
            "task_id": task_id,
            "status": "success",
            "video_result_url": url_video_terminado
        }
        
        response = requests.post(url_real, json=payload)
        print(f"Webhook enviado a n8n: {response.status_code}")

    except Exception as e:
        estados_tareas[task_id] = "error"
        print(f"Error procesando video: {str(e)}")

@app.post("/transcode")
def iniciar_transcodificacion(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pendiente"
    background_tasks.add_task(procesar_video, task_id, datos)
    return {"id": task_id, "status": "pending"}

@app.get("/")
def read_root():
    return {"mensaje": "¡Tu servicio está live!"}
