from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

# 1. ESTO DEBE IR PRIMERO (antes de cualquier @app.post o @app.get)
app = FastAPI()

estados_tareas = {}

# 2. Tus rutas continúan aquí abajo
@app.post("/transcode")
def crear_trabajo(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    # background_tasks.add_task(proceso_ffmpeg_real, task_id)
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return {"id": task_id, "status": estados_tareas[task_id]}

@app.get("/download/{task_id}")
def descargar_video(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    ruta_archivo = f"video_procesado_{task_id}.mp4" 
    
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo de video no encontrado en el servidor")
        
    return FileResponse(ruta_archivo, media_type="video/mp4", filename="video_final.mp4")
