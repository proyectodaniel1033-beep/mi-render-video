import subprocess
import uuid
from fastapi import BackgroundTasks, FastAPI, HTTPException

app = FastAPI()

# Diccionario temporal en memoria para almacenar el estado de las tareas
estados_tareas = {}


def tarea_ffmpeg_en_segundo_plano(task_id: str):
  print(f"-> [INICIO] Tarea iniciada: {task_id}")
  try:
    # Marcamos como pendiente al arrancar
    estados_tareas[task_id] = "pendiente"

    # ==========================================
    # AQUÍ DEBES COLOCAR TU COMANDO REAL DE FFMEPG
    # Ejemplo:
    # comando = ["ffmpeg", "-i", "entrada.mp4", "salida.mp4"]
    # subprocess.run(comando, check=True)
    # ==========================================

    # Simulación temporal de procesamiento (puedes cambiarlo o quitarlo cuando pongas tu FFmpeg real)
    import time

    time.sleep(5)

    # PASO CLAVE: Al terminar con éxito, actualizamos a "completado" para romper el ciclo en n8n
    estados_tareas[task_id] = "completado"
    print(f"-> [EXITO] Tarea completada con éxito: {task_id}")

  except Exception as e:
    # Si ocurre cualquier error (como falta de FFmpeg o archivos no encontrados),
    # lo guardamos como "error" para evitar bucles infinitos
    estados_tareas[task_id] = "error"
    print(f"-> [ERROR] Falló la tarea {task_id}: {str(e)}")


@app.post("/renderizar")
def iniciar_renderizado(background_tasks: BackgroundTasks):
  # Generamos un ID único para la tarea
  task_id = str(uuid.uuid4())

  # Inicializamos el estado
  estados_tareas[task_id] = "pendiente"

  # Lanzamos la tarea en segundo plano
  background_tasks.add_task(tarea_ffmpeg_en_segundo_plano, task_id)

  return {"task_id": task_id, "estado": "pendiente"}


@app.get("/status/{task_id}")
def obtener_estado(task_id: str):
  # Si el ID no existe en memoria, por seguridad respondemos pendiente o error
  estado_actual = estados_tareas.get(task_id, "pendiente")
  return {"estado": estado_actual}

FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
