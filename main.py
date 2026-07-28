from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

app = FastAPI()

# Diccionario temporal de estados
estados_tareas = {}
CARPETA_VIDEOS = "/tmp"

def proceso_ffmpeg_real(task_id: str):
    try:
        estados_tareas[task_id] = "processing" # O "procesando" según prefieras
        
        # --- AQUÍ VA TU COMANDO REAL DE FFMPEG ---
        # Ejemplo con os.system o subprocess para procesar tu video real:
        ruta_archivo = os.path.join(CARPETA_VIDEOS, f"{task_id}.mp4")
        
        # Simulación robusta o comando real:
        # os.system(f"ffmpeg -i entrada.mp4 {ruta_archivo}")
        
        # Si estás haciendo pruebas, asegúrate de crear un archivo válido o usar os.system
        with open(ruta_archivo, "wb") as f:
            f.write(b"contenido de video falso para prueba")
            
        estados_tareas[task_id] = "completed"
    except Exception as e:
        estados_tareas[task_id] = "failed"

@app.post("/transcode")
def crear_trabajo(background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    background_tasks.add_task(proceso_ffmpeg_real, task_id)
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return {"id": task_id, "estado": estados_tareas[task_id]}
from fastapi.responses import FileResponse
import os

@app.get("/download/{task_id}")
def descargar_video(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    # Asegúrate de que esta sea la ruta donde guardas tu archivo de video procesado
    ruta_archivo = f"video_procesado_{task_id}.mp4" 
    
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo de video no encontrado en el servidor")
        
    return FileResponse(ruta_archivo, media_type="video/mp4", filename="video_final.mp4")
