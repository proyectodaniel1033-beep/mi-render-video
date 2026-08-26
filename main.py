import os
import subprocess
import shutil
import uuid
import re
import edge_tts
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(title="Video Renderer Definitivo - Producción")

# Carpeta base para sesiones de render
BASE_UPLOAD_DIR = "upload_sessions"
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

# Ruta raíz para el despertador de n8n
@app.get("/")
async def root():
    return {"status": "ok", "message": "Servidor despierto y listo"}
    
# 1. Generador de voz con limpieza de etiquetas de pensamiento del LLM
@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    try:
        texto_limpio = re.sub(r'<think>.*?</think>', '', payload.text, flags=re.DOTALL)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
        
        if not texto_limpio:
            raise HTTPException(status_code=400, detail="El texto para la voz está vacío.")

        output_file = f"temp_audio_{uuid.uuid4()}.mp3"
        communicate = edge_tts.Communicate(texto_limpio, payload.voice)
        await communicate.save(output_file)
        
        return FileResponse(output_file, media_type="audio/mpeg", filename="audio.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Recepción de videos individuales por sesión desde el loop de n8n
@app.post("/unir-binarios-individual")
async def recibir_video(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        session_path = os.path.join(BASE_UPLOAD_DIR, session_id)
        os.makedirs(session_path, exist_ok=True)
        
        file_path = os.path.join(session_path, f"{uuid.uuid4()}.mp4")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"status": "ok", "message": "Video guardado correctamente", "session": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Concatenación final con FFmpeg (Normalizado y con Faststart para YouTube)
@app.post("/finalizar-render")
async def finalizar_render(session_id: str = Form(...)):
    session_path = os.path.join(BASE_UPLOAD_DIR, session_id)
    if not os.path.exists(session_path):
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")

    try:
        files = [os.path.join(session_path, f) for f in os.listdir(session_path) if f.endswith(".mp4")]
        
        if not files:
            raise HTTPException(status_code=400, detail="No hay videos acumulados en esta sesión.")

        files.sort()
        
        list_file_path = os.path.join(session_path, "list.txt")
        output_video = os.path.join(session_path, "final_unido.mp4")

        with open(list_file_path, "w") as f:
            for file_path in files:
                f.write(f"file '{os.path.abspath(file_path)}'\n")

        # COMANDO ULTRA RÁPIDO: Usa preset ultrafast para evitar el error 502 en Render
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file_path,
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_video
        ]
        
        result = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {result.stderr.decode('utf-8')}")

        return FileResponse(output_video, media_type="video/mp4", filename="video_final.mp4")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Limpieza posterior de los fragmentos individuales
        if os.path.exists(session_path):
            for f in os.listdir(session_path):
                file_path = os.path.join(session_path, f)
                if f != "final_unido.mp4" and os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
