import os
import subprocess
import tempfile
from typing import List, Union, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import edge_tts
import json

app = FastAPI(title="Video y Voz Renderer Microservice", version="1.3.1")

class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/unir-videos")
async def unir_videos(payload: VideoRequest):
    temp_files = []
    normalized_files = []
    list_file_path = None
    output_video = None
    
    try:
        raw_data = payload.urls
        urls_limpias = []

        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                pass

        def extraer_urls(obj):
            if isinstance(obj, str):
                cleaned = obj.strip('"').strip("'").replace('\\"', '"')
                if cleaned.startswith("http"):
                    urls_limpias.append(cleaned)
            elif isinstance(obj, list):
                for item in obj:
                    extraer_urls(item)
            elif isinstance(obj, dict):
                for val in obj.values():
                    extraer_urls(val)

        extraer_urls(raw_data)

        if not urls_limpias:
            raise HTTPException(status_code=400, detail="No se pudieron extraer URLs válidas.")

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'} 
        
        # 1. Descargar y normalizar de uno en uno para ahorrar RAM en Render
        for i, url in enumerate(urls_limpias):
            try:
                clean_url = url.strip('"').strip("'")
                response = requests.get(clean_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    t_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    t_file.write(response.content)
                    t_file.close()
                    temp_files.append(t_file.name)

                    # Normalizamos inmediatamente para liberar el video pesado original
                    norm_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    norm_path.close()
                    
                    # Bajamos a 640x360 para evitar que Render se quede sin memoria (Error 502)
                    cmd_norm = [
                        "ffmpeg", "-y", "-i", t_file.name,
                        "-vf", "scale=640:360:force_original_aspect_ratio=increase,crop=640:360",
                        "-r", "30", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an", norm_path.name
                    ]
                    subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    normalized_files.append(norm_path.name)
                    
                    # Borramos el temporal pesado original de inmediato
                    os.unlink(t_file.name)
            except Exception as e:
                print(f"Error procesando video {i}: {e}")

        if not normalized_files:
            raise HTTPException(status_code=500, detail="No se pudo procesar ningún video.")

        # 2. Crear archivo de lista para FFmpeg
        list_file_path = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
        for f_path in normalized_files:
            safe_path = f_path.replace("\\", "/")
            list_file_path.write(f"file '{safe_path}'\n")
        list_file_path.close()

        output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        output_video.close()

        # 3. Concatenar los clips ya normalizados
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file_path.name,
            "-c", "copy", output_video.name
        ]
        
        result = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg concat: {result.stderr.decode('utf-8')}")

        return FileResponse(
            output_video.name,
            media_type="video/mp4",
            filename="secuencia_videos_unida.mp4"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    finally:
        # Limpieza de seguridad de archivos temporales sobrantes
        for f in temp_files + normalized_files:
            try:
                if os.path.exists(f): os.unlink(f)
            except: pass
        if list_file_path and os.path.exists(list_file_path.name):
            try: os.unlink(list_file_path.name)
            except: pass

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
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
