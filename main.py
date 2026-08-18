import os
import subprocess
import tempfile
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Video Renderer Elite API", version="1.3.1")

# --- Modelos ---
class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

# --- Endpoints ---

@app.post("/render-final")
async def render_final(video_url: str = Form(...), audio: UploadFile = File(...)):
    """
    Procesa video desde URL y audio desde binario. 
    Uso de contextos para limpieza automática de archivos.
    """
    # Usamos TemporaryDirectory para asegurar que todo se borre al terminar la petición
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = os.path.join(temp_dir, "input_video.mp4")
        audio_path = os.path.join(temp_dir, "input_audio.mp3")
        output_path = os.path.join(temp_dir, "output.mp4")

        try:
            # 1. Descarga eficiente
            response = requests.get(video_url, stream=True, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Error al descargar el video fuente.")
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 2. Guardado de audio binario
            with open(audio_path, 'wb') as f:
                f.write(await audio.read())

            # 3. Procesamiento FFmpeg (Hardened)
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"FFmpeg Error: {result.stderr}")

            # Devolvemos el archivo directamente
            return FileResponse(output_path, media_type="video/mp4", filename="final_render.mp4")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallo en el pipeline: {str(e)}")

@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    try:
        communicate = edge_tts.Communicate(payload.text, payload.voice)
        await communicate.save(tmp.name)
        return FileResponse(tmp.name, media_type="audio/mpeg", filename="audio.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
