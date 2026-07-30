import os
import uuid
import subprocess
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

# Diccionario en memoria para almacenar el estado de las tareas
estados_tareas = {}

class TranscodeRequest(BaseModel):
    video_url: str
    audio_url: str
    webhook_url: str
    
def procesar_video(task_id: str, datos: TranscodeRequest):
    ruta_video_entrada = f"input_video_{task_id}.mp4"
    ruta_audio_entrada = f"input_audio_{task_id}.mp3"
    ruta_salida = f"output_video_{task_id}.mp4"

    try:
        estados_tareas[task_id] = "processing"

        # 1. Descargar el video de la URL
        response_video = requests.get(datos.video_url)
        with open(ruta_video_entrada, "wb") as f:
            f.write(response_video.content)

        # 2. Descargar el audio de la URL de forma segura
        response_audio = requests.get(datos.audio_url)
        with open(ruta_audio_entrada, "wb") as f:
            f.write(response_audio.content)

        # 3. Construir el comando de FFmpeg para fusionar video y audio
        comando = [
            "ffmpeg",
            "-y",
            "-i", ruta_video_entrada,
            "-i", ruta_audio_entrada,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            ruta_salida
        ]

        # 4. Ejecutar FFmpeg
        subprocess.run(comando, check=True)
        
        # Si todo sale bien
        estados_tareas[task_id] = "completed"
        requests.get(datos.webhook_url)

    except Exception as e:
        print(f"Error en el proceso: {e}")
        estados_tareas[task_id] = "failed"

    finally:
        # Limpiar archivos temporales locales del servidor
        for ruta in [ruta_video_entrada, ruta_audio_entrada, ruta_salida]:
            if os.path.exists(ruta):
                try:
                    os.remove(ruta)
                except Exception:
                    pass

from fastapi import Request, HTTPException

@app.post("/transcode")
async def iniciar_transcodificacion(request: Request):
    try:
        data = await request.json()
        print("LO QUE LLEGÓ DESDE N8N:", data)
        
        # Validamos manualmente para ver qué falta
        video_url = data.get("video_url")
        audio_url = data.get("audio_url")
        webhook_url = data.get("webhook_url")
        
        if not video_url or not audio_url or not webhook_url:
            print(f"Faltan datos. Llegó -> video: {video_url}, audio: {audio_url}, webhook: {webhook_url}")
            raise HTTPException(status_code=422, detail="Faltan campos obligatorios")
            
        return {"estado": "ok"}
    except Exception as e:
        print("Error:", str(e))
        raise HTTPException(status_code=422, detail=str(e))

    # Ejecutar en segundo plano para que Render no corte la petición HTTP
    background_tasks.add_task(procesar_video, task_id, datos)

    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    estado = estados_tareas.get(task_id, "not_found")
    return {"id": task_id, "status": estado}
