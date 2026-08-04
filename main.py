import os
import subprocess
import requests
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Headers para evitar bloqueo de descarga (ej. Catbox)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

@app.post("/transcode")
async def transcode_video(audio_url: str = Form(...), video_urls: str = Form(...)):
    """
    Recibe la URL del audio de Catbox y una lista/cadena de URLs de Pexels.
    Descarga los recursos, los procesa con FFmpeg y genera un video final.
    """
    try:
        # 1. Preparar directorios temporales
        os.makedirs("/tmp/media", exist_ok=True)
        
        # Parsear las URLs de los videos (asumiendo que llegan separadas por coma o como texto)
        urls_list = [v.strip() for v in video_urls.split(",") if v.strip()]
        
        if not urls_list:
            raise HTTPException(status_code=400, detail="No se proporcionaron URLs de video.")

        # 2. Descargar el archivo de audio de Catbox de forma segura
        audio_path = "/tmp/media/audio.mp3"
        audio_res = requests.get(audio_url, headers=HEADERS, stream=True)
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar el audio desde Catbox: {audio_res.status_code}")
        
        with open(audio_path, "wb") as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Descargar cada clip de video de Pexels
        video_files = []
        for i, v_url in enumerate(urls_list):
            v_path = f"/tmp/media/video_{i}.mp4"
            v_res = requests.get(v_url, headers=HEADERS, stream=True)
            if v_res.status_code == 200:
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de Pexels.")

        # 4. Crear archivo de lista para concatenar con FFmpeg
        concat_list_path = "/tmp/media/concat_list.txt"
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        # 5. Procesar con FFmpeg (Concat videos + Ajustar al audio / duracion aprox)
        output_video_path = "/tmp/media/output_final.mp4"
        
        # Comando para concatenar videos y sincronizar con el audio de fondo
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",  # Ajusta la duración total al tamaño del audio
            output_video_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True)

        # 6. Retornar el archivo de video resultante hacia n8n
        return FileResponse(output_video_path, media_type="video/mp4", filename="final_video.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
