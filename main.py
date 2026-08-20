import os
import subprocess
import tempfile
import re
from typing import List, Union
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts
import uvicorn

app = FastAPI(title="Video y Voz Renderer Pro", version="2.1.0")

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/unir-binarios")
async def unir_binarios(files: Union[UploadFile, List[UploadFile]] = File(...)):
    temp_dir = tempfile.mkdtemp()
    list_file_path = os.path.join(temp_dir, "list.txt")
    output_video = os.path.join(temp_dir, "final.mp4")
    
    # Asegurarnos de que siempre sea una lista, sin importar cómo lo mande n8n
    if not isinstance(files, list):
        files = [files]
    
    try:
        with open(list_file_path, "w") as f:
            for i, file in enumerate(files):
                file_path = os.path.join(temp_dir, f"{i}.mp4")
                content = await file.read()
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                # Normalizar a 720p para asegurar compatibilidad
                norm_path = os.path.join(temp_dir, f"norm_{i}.mp4")
                cmd_norm = [
                    "ffmpeg", "-y", "-i", file_path, 
                    "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", 
                    "-r", "30", "-c:v", "libx264", "-crf", "23", "-an", norm_path
                ]
                subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                f.write(f"file '{norm_path}'\n")

        # Concatenar
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
            "-i", list_file_path, "-c", "copy", output_video
        ]
        result = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg concat: {result.stderr.decode('utf-8')}")

        return FileResponse(output_video, media_type="video/mp4", filename="video_largo_unido.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    try:
        texto_original = payload.text
        if not texto_original:
            raise HTTPException(status_code=400, detail="El texto para la voz está vacío.")

        # Limpiar etiquetas <think>...</think> y saltos de línea sobrantes del LLM
        texto_limpio = re.sub(r'<think>.*?</think>', '', texto_original, flags=subprocess.re.DOTALL if hasattr(subprocess, 're') else re.DOTALL)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()

        if not texto_limpio:
            texto_limpio = texto_original

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_file.close()

        communicate = edge_tts.Communicate(texto_limpio, payload.voice)
        await communicate.save(output_file.name)

        return FileResponse(
            output_file.name, 
            media_type="audio/mpeg", 
            filename="cancion_generada.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la voz: {str(e)}")

@app.post("/render-final")
async def render_final(video: UploadFile = File(...), audio: UploadFile = File(...)):
    try:
        video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        
        video_path.write(await video.read())
        video_path.close()
        
        audio_path.write(await audio.read())
        audio_path.close()
        output_path.close()

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path.name,
            "-i", audio_path.name,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",
            output_path.name
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg render final: {result.stderr.decode('utf-8')}")

        return FileResponse(
            output_path.name,
            media_type="video/mp4",
            filename="video_final_con_audio.mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en render final: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
