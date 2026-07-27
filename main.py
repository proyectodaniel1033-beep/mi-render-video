import os
import uuid
import subprocess
import requests
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

DB_FILE = "/tmp/jobs.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

class VideoRequest(BaseModel):
    video_url: str
    audio_url: str

def process_video_background(job_id: str, data: VideoRequest):
    session_id = job_id
    temp_video = f"/tmp/{session_id}_video.mp4"
    temp_audio = f"/tmp/{session_id}_audio.mp3"
    output_video = f"/tmp/{session_id}_output.mp4"

    try:
        db = load_db()
        db[job_id] = {"status": "processing"}
        save_db(db)

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

        # Unir Audio y Video con FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", temp_video,
            "-i", temp_audio,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_video
        ]

        subprocess.run(cmd, check=True)

        db = load_db()
        db[job_id] = {"status": "completed", "file_path": output_video}
        save_db(db)

    except Exception as e:
        db = load_db()
        db[job_id] = {"status": "failed", "error": str(e)}
        save_db(db)
    
    finally:
        for path in [temp_video, temp_audio]:
            if os.path.exists(path):
                os.remove(path)

@app.post("/render")
def start_render(data: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    db = load_db()
    db[job_id] = {"status": "queued"}
    save_db(db)
    
    background_tasks.add_task(process_video_background, job_id, data)
    return {"id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    db = load_db()
    if job_id not in db:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = db[job_id]
    
    if job["status"] == "completed":
        return {"status": "completed", "id": job_id}
    elif job["status"] == "failed":
        return {"status": "failed", "error": job.get("error")}
    
    return {"status": job["status"], "id": job_id}

@app.get("/download/{job_id}")
def download_video(job_id: str):
    db = load_db()
    if job_id not in db or db[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="El video aún no está listo o no existe")
    
    file_path = db[job_id]["file_path"]
    return FileResponse(file_path, media_type="video/mp4", filename="output.mp4")
