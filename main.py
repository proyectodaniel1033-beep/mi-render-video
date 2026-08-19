import os
import subprocess
import tempfile
from typing import List, Union, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import edge_tts

app = FastAPI(title="Video y Voz Renderer Microservice", version="1.2.0")

class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

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

        # --- PROCESO DE DESCARGA Y CONCATENACIÓN CON FFMPEG ---
        temp_files = []
        list_file_path = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
        output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        output_video.close()

        # 1. Descargar cada video temporalmente con cabeceras para evitar bloqueos
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'} 
        for url in urls_limpias:
            try:
                # Limpiamos posibles comillas extra que pueden venir en el string de n8n
                clean_url = url.strip('"').strip("'")
                response = requests.get(clean_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    t_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    t_file.write(response.content)
                    t_file.close()
                    temp_files.append(t_file.name)
                else:
                    print(f"Error {response.status_code} al descargar: {clean_url}")
            except Exception as e:
                print(f"Error descargando {url}: {e}")

        # 2. Crear el archivo de texto para la concatenación segura de FFmpeg
        for f_path in temp_files:
            safe_path = f_path.replace("\\", "/")
            list_file_path.write(f"file '{safe_path}'\n")
        list_file_path.close()

        # 3. Ejecutar FFmpeg: Normalizar y luego concatenar
        # Primero re-codificamos cada clip a un formato idéntico (720p, 30fps)
        normalized_files = []
        for i, f_path in enumerate(temp_files):
            norm_path = f"norm_{i}.mp4"
            cmd_norm = [
                "ffmpeg", "-y", "-i", f_path,
                "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
                "-r", "30", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", norm_path
            ]
            subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            normalized_files.append(norm_path)

        # Ahora creamos el archivo de lista con los normalizados
        list_file_path = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".txt")
        for f_path in normalized_files:
            list_file_path.write(f"file '{os.path.abspath(f_path)}'\n")
        list_file_path.close()

        # Concatenar
        cmd_concat = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file_path.name,
            "-c", "copy", output_video.name
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Limpiar archivos temporales individuales
        for f_path in temp_files:
            try:
                os.unlink(f_path)
            except:
                pass
        try:
            os.unlink(list_file_path.name)
        except:
            pass

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg al unir videos: {result.stderr.decode('utf-8')}")

        # 4. Retornar el archivo MP4 unificado listo para el nodo de descarga en n8n
        return FileResponse(
            output_video.name,
            media_type="video/mp4",
            filename="secuencia_videos_unida.mp4"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

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
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {result.stderr.decode('utf-8')}")

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
