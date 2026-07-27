from fastapi.responses import FileResponse
import os

# Ruta donde guardas el video procesado
OUTPUT_DIR = "/tmp"  # O la carpeta donde guardes tus videos generados


@app.get("/download/{task_id}")
def descargar_video(task_id: str):
  # Busca el archivo generado (ejemplo: task_id.mp4)
  file_path = os.path.join(OUTPUT_DIR, f"{task_id}.mp4")

  if os.path.exists(file_path):
    return FileResponse(
        file_path, media_type="video/mp4", filename="video_final.mp4"
    )

  return {"error": "Archivo no encontrado o proceso en curso"}
