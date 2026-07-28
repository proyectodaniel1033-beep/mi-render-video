import subprocess
import uuid
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI()

estados_tareas = {}

# Definimos el formato de los datos que recibirá el POST desde n8n
class VideoRequest(BaseModel):
    imagen_url: str
    audio_url: str

def proceso_ffmpeg_real(task_id: str, imagen_url: str, audio_url: str):
    ruta_imagen = f"temp_img_{task_id}.jpg"
    ruta_audio = f"temp_audio_{task_id}.mp3"
    ruta_archivo = f"video_procesado_{task_id}.mp4"
    duracion_segundos = "30"  # O el tiempo exacto que prefieras
    
    try:
        # 1. Descargar la imagen gratuita de Pexels
        img_data = requests.get(imagen_url).content
        with open(ruta_imagen, 'wb') as handler:
            handler.write(img_data)
            
        # 2. Descargar el archivo de audio generado
        audio_data = requests.get(audio_url).content
        with open(ruta_audio, 'wb') as handler:
            handler.write(audio_data)
            
        # 3. Comando FFmpeg uniendo la imagen descargada y el audio con tiempo controlado
        comando = [
            "ffmpeg",
            "-loop", "1",
            "-i", ruta_imagen,
            "-i", ruta_audio,
            "-t", duracion_segundos,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            ruta_archivo
        ]
        
        subprocess.run(comando, check=True)
        estados_tareas[task_id] = "completed"
        
    except Exception as e:
        print(f"Error en el proceso: {e}")
        estados_tareas[task_id] = "error"

@app.post("/transcode")
def crear_trabajo(request: VideoRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    # Pasamos las URLs recibidas desde n8n a la tarea en segundo plano
    background_tasks.add_task(proceso_ffmpeg_real, task_id, request.imagen_url, request.audio_url)
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    return {"status": estados_tareas.get(task_id, "not_found")}
