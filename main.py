import uuid
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

# Diccionario temporal para guardar los estados
estados_tareas = {}


def tarea_ffmpeg_en_segundo_plano(task_id: str):
  try:
    estados_tareas[task_id] = "pendiente"

    # Simulación de proceso (aquí irá tu FFmpeg después)
    import time

    time.sleep(5)

    # LA CLAVE: Cambia el estado a "completado" al terminar
    estados_tareas[task_id] = "completado"
    print(f"Tarea {task_id} finalizada con éxito.")
  except Exception as e:
    estados_tareas[task_id] = "error"
    print(f"Error en tarea {task_id}: {e}")


@app.post("/renderizar")
def iniciar_renderizado(background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  estados_tareas[task_id] = "pendiente"
  background_tasks.add_task(tarea_ffmpeg_en_segundo_plano, task_id)
  return {"task_id": task_id, "estado": "pendiente"}


@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
  estado_actual = estados_tareas.get(task_id, "pendiente")
  return {"estado": estado_actual}
