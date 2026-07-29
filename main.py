from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import requests
import subprocess
import uuid
import os

app = FastAPI()

# Diccionario temporal para guardar el estado de las tareas
estados_tareas = {}

class TranscodeRequest(BaseModel):
    video_url: str
    audio_url: str

def procesar_video(task_id: str, video_url: str, audio_url: str):
    try:
        estados_tareas[task_id] = "processing"

        ruta_video_entrada = f"input_video_{task_id}.mp4"
        ruta_audio_entrada = f"input_audio_{task_id}.mp3"
        ruta_salida = f"output_video_{task_id}.mp4"

        # 1. Descargar el video de entrada automáticamente
        video_data = requests.get(video_url).content
        with open(ruta_video_entrada, "wb") as f:
            f.write(video_data)

        # 2. Descargar el audio de entrada automáticamente
        audio_data = requests.get(audio_url).content
        with open(ruta_audio_entrada, "wb") as f:
            f.write(audio_data)

        # 3. Comando FFmpeg para combinar el video y el audio automatizados
        comando = [
            "ffmpeg",
            "-i", ruta_video_entrada,
            "-i", ruta_audio_entrada,
            "-c:v", "copy",       # Copia el video sin recodificar para mayor velocidad
            "-c:a", "aac",        # Codifica el audio en AAC estándar
            "-shortest",          # Corta cuando el archivo más corto termine
            ruta_salida
        ]

        subprocess.run(comando, check=True)
        estados_tareas[task_id] = "completed"

    except Exception as e:
        print(f"Error en el proceso: {e}")
        estados_tareas[task_id] = "failed"
        
    finally:
        # Limpiar archivos temporales locales para no saturar el servidor
        for ruta in [ruta_video_entrada, ruta_audio_entrada]:
            if os.path.exists(ruta):
                os.remove(ruta)

@app.post("/transcode")
def iniciar_transcode(datos: TranscodeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"

    # Ejecutar en segundo plano para que Render no corte la petición HTTP
    background_tasks.add_task(procesar_video, task_id, datos.video_url, datos.audio_url)

    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def verificar_estado(task_id: str):
    estado = estados_tareas.get(task_id, "not_found")
    return {"id": task_id, "status": estado}
