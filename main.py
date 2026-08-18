import os
import subprocess
import tempfile
from typing import List, Union, Any
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Video Renderer Elite API", version="1.4.0")

# --- Modelos de Petición ---
class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"


# --- Endpoint 1: Unir/Limpiar URLs de Videos ---
@app.post("/unir-videos")
async def unir_videos(payload: VideoRequest):
    try:
        raw_data = payload.urls
        urls_limpias = []

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, list):
                    urls_limpias.extend([str(i) for i in item if i])
                elif isinstance(item, dict):
                    for val in item.values():
                        if isinstance(val, list):
                            urls_limpias.extend([str(i) for i in val if i])
                        elif val:
                            urls_limpias.append(str(val))
                elif item:
                    urls_limpias.append(str(item))
        elif isinstance(raw_data, dict):
            for val in raw_data.values():
                if isinstance(val, list):
                    urls_limpias.extend([str(i) for i in val if i])
                elif val:
                    urls_limpias.append(str(val))
        elif isinstance(raw_data, str):
            urls_limpias.append(raw_data)

        if not urls_limpias:
            raise HTTPException(status_code=400, detail="La lista de URLs está vacía o el formato no es válido.")

        return {
            "status": "success",
            "message": "Videos procesados correctamente",
            "total_urls": len(urls_limpias),
            "urls": urls_limpias
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


# --- Endpoint 2: Generar Voz con edge-tts ---
@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    try:
        if not payload.text:
            raise HTTPException(status_code=400, detail="El texto para la voz está vacío.")

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_file.close()

        communicate = edge_tts.Communicate(payload.text, payload.voice)
        await communicate.save(output_file.name)

        return FileResponse(
            output_file.name, 
            media_type="audio/mpeg", 
            filename="audio_generado.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la voz: {str(e)}")


# --- Endpoint 3: Render Final (Fusionar Video URL + Audio Binario con FFmpeg) ---
@app.post("/render-final")
async def render_final(video_url: str = Form(...), audio: UploadFile = File(...)):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = os.path.join(temp_dir, "input_video.mp4")
            audio_path = os.path.join(temp_dir, "input_audio.mp3")
            output_path = os.path.join(temp_dir, "output_final.mp4")

            # 1. Descargar el video de Cloudinary de forma segura
            response = requests.get(video_url, stream=True, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="No se pudo descargar el video fuente desde la URL.")
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 2. Guardar el archivo de audio recibido en binario
            with open(audio_path, 'wb') as f:
                content = await audio.read()
                f.write(content)

            # 3. Ejecutar FFmpeg para unir video y audio
            cmd = [
             "ffmpeg",
             "-y",
             "-i",
             video_path,
             "-i",
             audio_path,
             "-map",
             "0:v:0",  # Toma estrictamente el video del primer archivo (video)
             "-map",
             "1:a:0",  # Toma estrictamente el audio del segundo archivo (audio)
             "-c:v",
             "copy",
             "-c:a",
             "aac",
             "-b:a",
             "192k",
             "-shortest",
             output_path,
             ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {result.stderr}")

            return FileResponse(
                output_path,
                media_type="video/mp4",
                filename="video_final_con_audio.mp4"
            )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en render final: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
