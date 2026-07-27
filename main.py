import os
import uuid
import subprocess
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Diccionario temporal en memoria para guardar el estado de los trabajos
# (En producción se usaría una base de datos, pero para n8n esto funciona perfecto)
jobs_db = {}

class VideoRequest(BaseModel):
    video_url: str
    audio_url: str

def process_video_background(job_id: str, data: VideoRequest):
    session_id = job_id
    temp_video = f"/tmp/{session_id}_video.mp4"
    temp_audio = f"/tmp/{session_id}_audio.mp3"
    output_video = f"/tmp/{session_id}_output.mp4"

    try:
        # Actualizar estado a procesando
        jobs_db[job_id] = {"status": "processing"}

        # Descargar Video
        res_v = requests.get(data.video_url, stream=True)
        with open(temp_video, 'wb') as f:
            for chunk in res_v.iter_content(chunk_size=8192):
                f.write(chunk)

        # Descargar Audio
        res_a = requests.get(data.audio_url, stream=True)
        with open(temp_audio, 'wb') as f:
            for chunk in res_a.iter_content(chunk_size=8192):
                f.write(chunk)

        # Unir Audio y Video con FFmpeg (aquí aplica tu -stream_loop y -shortest para los 2 minutos)
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", temp_video,
            "-i", temp_audio,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_video
        ]

        subprocess.run(cmd, check=True)

        # Marcar como completado
        jobs_db[job_id] = {"status": "completed", "file_path": output_video}

    except Exception as e:
        jobs_db[job_id] = {"status": "failed", "error": str(e)}
    
    finally:
        # Limpiar archivos temporales de entrada
        for path in [temp_video, temp_audio]:
            if os.path.exists(path):
                os.path.exists(path) # o pass

@app.post("/render")
def start_render(data: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {"status": "queued"}
    
    # Ejecutar el renderizado en segundo plano para no bloquear la respuesta HTTP
    background_tasks.add_task(process_video_background, job_id, data)
    
    # Devolver inmediatamente el ID del trabajo a n8n
    return {"id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = jobs_db[job_id]
    
    # Si ya terminó, devolvemos un JSON indicando que está listo
    if job["status"] == "completed":
        return {"status": "completed", "id": job_id}
    elif job["status"] == "failed":
        return {"status": "failed", "error": job.get("error")}
    
    return {"status": job["status"], "id": job_id}

@app.get("/download/{job_id}")
def download_video(job_id: str):
    if job_id not in jobs_db or jobs_db[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="El video aún no está listo o no existe")
    
    file_path = jobs_db[job_id]["file_path"]
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")
