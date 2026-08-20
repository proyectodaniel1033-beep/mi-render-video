import os
import subprocess
import shutil
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse

app = FastAPI(title="Video Renderer Persistente")

# Carpeta base para sesiones de render
BASE_UPLOAD_DIR = "upload_sessions"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

@app.post("/unir-binarios-individual")
async def recibir_video(
    session_id: str = Form(...), # n8n debe enviar un ID único para cada tanda de videos
    file: UploadFile = File(...)
):
    # Creamos una carpeta específica para esta tanda de videos
    session_path = os.path.join(BASE_UPLOAD_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)
    
    # Guardamos el video
    file_path = os.path.join(session_path, f"{uuid.uuid4()}.mp4")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"message": "Video guardado", "session": session_id}

@app.post("/finalizar-render")
async def finalizar_render(session_id: str = Form(...)):
    session_path = os.path.join(BASE_UPLOAD_DIR, session_id)
    if not os.path.exists(session_path):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Lista de archivos para FFmpeg
    files = [os.path.join(session_path, f) for f in os.listdir(session_path) if f.endswith(".mp4")]
    list_file_path = os.path.join(session_path, "list.txt")
    output_video = os.path.join(session_path, "final_unido.mp4")

    with open(list_file_path, "w") as f:
        for file_path in files:
            f.write(f"file '{file_path}'\n")

    # Comando de unión
    cmd_concat = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", output_video]
    subprocess.run(cmd_concat)

    # Devolvemos el video y luego limpiamos
    return FileResponse(output_video, media_type="video/mp4", filename="final.mp4")
