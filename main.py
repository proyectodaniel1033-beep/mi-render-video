import time
import uuid
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

estados_tareas = {}


def tarea_simulada(task_id: str):
  try:
    print(f"Iniciando tarea: {task_id}")
    time.sleep(10)  # Simula el tiempo de renderizado
    estados_tareas[task_id] = "completado"
    print(f"Tarea {task_id} completada con éxito.")
  except Exception as e:
    estados_tareas[task_id] = "error"
    print(f"Error en tarea {task_id}: {e}")


@app.post("/renderizar")
def iniciar(background_tasks: BackgroundTasks):
  task_id = str(uuid.uuid4())
  estados_tareas[task_id] = "pendiente"
  background_tasks.add_task(tarea_simulada, task_id)
  return {"task_id": task_id, "estado": "pendiente"}


@app.get("/status/{task_id}")
def estado(task_id: str):
  return {"estado": estados_tareas.get(task_id, "pendiente")}
