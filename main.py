import os
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

# Diccionario temporal para estados
estados_tareas = {}

def proceso_ffmpeg_real(task_id: str, video_url: str):
    try:
        # Define el nombre del archivo basado en el ID de la tarea
        ruta_archivo = f"video_procesado_{task_id}.mp4"
        
        # AQUÍ ES DONDE DEBES EJECUTAR TU COMANDO DE FFPEG O DESCARGA
        # Por ejemplo, usando subprocess para descargar y procesar con FFmpeg:
        # comando = f"ffmpeg -i {video_url} -c:v libx264 {ruta_archivo}"
        # subprocess.run(comando, shell=True, check=True)
        
        # (Si estás haciendo pruebas, asegúrate de crear un archivo válido temporalmente):
        with open(ruta_archivo, "wb") as f:
            f.write(b"contenido de video falso para prueba")
            
        estados_tareas[task_id] = "completed"
    except Exception as e:
        estados_tareas[task_id] = "failed"

@app.post("/transcode")
def crear_trabajo(body: dict, background_tasks: BackgroundTasks):
    video_url = body.get("url")
    task_id = str(uuid.uuid4())
    estados_tareas[task_id] = "pending"
    
    # Pasamos la URL del video que viene de n8n a la tarea en segundo plano
    background_tasks.add_task(proceso_ffmpeg_real, task_id, video_url)
    return {"id": task_id, "status": "pending"}

@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return {"id": task_id, "estado": estados_tareas[task_id]}

@app.get("/download/{task_id}")
def descargar_video(task_id: str):
    if task_id not in estados_tareas:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    ruta_archivo = f"video_procesado_{task_id}.mp4"
    
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo de video no encontrado en el servidor")
        
    return FileResponse(ruta_archivo, media_type="video/mp4", filename="video_final.mp4")
