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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        ruta_video_entrada = f"input_video_{task_id}.mp4"
        ruta_audio_entrada = f"input_audio_{task_id}.mp3"
        ruta_salida = f"output_video_{task_id}.mp4"

        # 1. Descargar video
        r_video = requests.get(video_url, headers=headers, stream=True)
        with open(ruta_video_entrada, "wb") as f:
            for chunk in r_video.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Descargar audio
        r_audio = requests.get(audio_url, headers=headers, stream=True)
        with open(ruta_audio_entrada, "wb") as f:
            for chunk in r_audio.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Comando FFmpeg para combinar
        comando = [
            "ffmpeg",
            "-i", ruta_video_entrada,
            "-i", ruta_audio_entrada,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            ruta_salida
        ]
        
        # Descargar el audio de la URL a un archivo local temporal
    import requests
    ruta_audio_entrada = f"input_audio_{task_id}.mp3"
    
    response_audio = requests.get(datos.audio_url)
    with open(ruta_audio_entrada, "wb") as f:
        f.write(response_audio.content)

    # Ejecutar FFmpeg
    subprocess.run(comando, check=True)
    
    # Si todo sale bien, cambia a completed
    estados_tareas[task_id] = "completed"

except Exception as e:
    print(f"Error en el proceso: {e}")
    estados_tareas[task_id] = "failed"

finally:
    # Limpiar archivos temporales locales
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
