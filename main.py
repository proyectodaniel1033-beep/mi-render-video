import os
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Diccionario temporal de estados y carpeta de videos
estados_tareas = {}
CARPETA_VIDEOS = (  # Directorio donde guardas los videos generados por FFmpeg
    "/tmp"
)


def proceso_ffmpeg_real(task_id: str):
  try:
    estados_tareas[task_id] = "procesando"

    # --- AQUÍ VA TU COMANDO REAL DE FFPEG ---
    # Ejemplo: os.system(f"ffmpeg -i entrada.mp4 /tmp/{task_id}.mp4")
    # Para la prueba, simularemos la creación del archivo de video:
    ruta_archivo = os.path.join(CARPETA_VIDEOS, f"{task_id}.mp4")
    with open(ruta_archivo, "w") as f:
      f.write("contenido de video falso para prueba")
    # ----------------------------------------

    estados_tareas[task_id] = "completado"
  except Exception as e:
    estados_tareas[task_id] = "error"


@app.post("/renderizar")
def iniciar_render(background_tasks: BackgroundTasks):
  import uuid

  task_id = str(uuid.uuid4())
  estados_tareas[task_id] = "pendiente"
  background_tasks.add_task(proceso_ffmpeg_real, task_id)
  return {"task_id": task_id, "estado": "pendiente"}


@app.get("/status/{task_id}")
def ver_estado(task_id: str):
  return {"estado": estados_tareas.get(task_id, "pendiente")}


@app.get("/download/{task_id}")
def descargar_archivo(task_id: str):
  ruta_archivo = os.path.join(CARPETA_VIDEOS, f"{task_id}.mp4")
  if os.path.exists(ruta_archivo):
    return FileResponse(
        ruta_archivo, media_type="video/mp4", filename=f"video_{task_id}.mp4"
    )
  raise HTTPException(
      status_code=404, detail="El video aún no está listo o no existe"
  )
