import subprocess
import uuid
from fastapi import BackgroundTasks, FastAPI, HTTPException

app = FastAPI()

# Diccionario temporal en memoria para almacenar el estado de cada tarea de renderizado
# (Ejemplo: {"uuid-de-la-tarea": "pendiente"})
estados_tareas = {}


def tarea_ffmpeg_en_segundo_plano(task_id: str):
  try:
    # Actualizamos el estado a procesando o dejamos pendiente mientras trabaja
    estados_tareas[task_id] = "pendiente"

    # AQUÍ VA TU COMANDO DE FFEXPG REAL
    # Ejemplo simulado de procesamiento con subprocess:
    # comando = ["ffmpeg", "-i", "entrada.mp4", "salida.mp4"]
    # subprocess.run(comando, check=True)

    # Simulación de tiempo de renderizado (puedes quitar esto cuando pongas tu comando real)
    import time

    time.sleep(10)

    # ----------------------------------------------------
    # EL PASO CLAVE: Cuando FFmpeg termina con éxito,
    # cambiamos el estado exactamente a la palabra que busca n8n.
    # ----------------------------------------------------
    estados_tareas[task_id] = "completado"

  except Exception as e:
    # Si ocurre algún error en FFmpeg, lo marcamos como error para evitar bucles infinitos
    estados_tareas[task_id] = "error"
    print(f"Error procesando el video {task_id}: {e}")


@app.post("/renderizar")
def iniciar_renderizado(background_tasks: BackgroundTasks):
  # Generamos un ID único para esta tarea
  task_id = str(uuid.uuid4())

  # Inicializamos el estado
  estados_tareas[task_id] = "pendiente"

  # Lanzamos la función en segundo plano para que no bloquee la respuesta HTTP
  background_tasks.add_task(tarea_ffmpeg_en_segundo_plano, task_id)

  # Le devolvemos el task_id a n8n para que pueda empezar a consultar el estado
  return {"task_id": task_id, "estado": "pendiente"}


@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
  # Si el task_id no existe, por seguridad devolvemos pendiente o error
  estado_actual = estados_tareas.get(task_id, "pendiente")

  # n8n recibirá exactamente este JSON {"estado": "pendiente"} o {"estado": "completado"}
  return {"estado": estado_actual}
