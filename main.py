import os
import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import requests

app = FastAPI()

TEMP_DIR = "/tmp/media"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/transcode")
async def transcode_video(request: Request):
    try:
        data = await request.json()
        audio_url = data.get("audio_url")
        video_urls = data.get("videos", [])

        if not audio_url or not video_urls:
            raise HTTPException(status_code=400, detail="Faltan 'audio_url' o 'videos' en la petición.")

        # Headers para evitar bloqueos (User-Agent de navegador)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # 1. Descargar audio de Catbox de forma segura
        audio_path = os.path.join(TEMP_DIR, "audio.mp3")
        audio_res = requests.get(audio_url, headers=headers, stream=True)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar el audio de Catbox: {audio_res.status_code}")
        
        with open(audio_path, "wb") as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Descargar los videos de Pexels
        video_files = []
        for i, v_url in enumerate(video_urls):
            v_path = os.path.join(TEMP_DIR, f"video_{i}.mp4")
            v_res = requests.get(v_url, headers=headers, stream=True)
            if v_res.status_code == 200:
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de Pexels.")

        # 3. Crear archivo de lista para FFmpeg (concat demuxer)
        concat_list_path = os.path.join(TEMP_DIR, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                # FFmpeg requiere rutas absolutas o relativas seguras
                f.write(f"file '{v_path}'\n")

        output_path = os.path.join(TEMP_DIR, "output_final.mp4")

        # 4. Ejecutar FFmpeg para unir videos y añadir el audio principal
        # -shortest hace que termine cuando acabe el audio (aprox 2 minutos)
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]

        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_msg = process.stderr.decode("utf-8", errors="ignore")
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {error_msg}")

        # 5. Retornar el video final procesado
        return FileResponse(output_path, media_type="video/mp4", filename="output_final.mp4")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
