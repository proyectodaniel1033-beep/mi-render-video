import os
import subprocess
import requests
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

# Headers para evitar bloqueos de descarga en servidores externos (ej. Catbox)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.post("/transcode")
async def transcode_video(audio_url: str = Form(...), video_urls: str = Form(...)):
    """
    Recibe la URL del audio de Catbox y la cadena de URLs de Pexels.
    Descarga los recursos, los procesa con FFmpeg y retorna el archivo final.
    """
    try:
        # 1. Preparar el directorio temporal de trabajo
        tmp_dir = "/tmp/media"
        os.makedirs(tmp_dir, exist_ok=True)
        
        # Parsear las URLs de los videos de Pexels separadas por comas
        urls_list = [v.strip() for v in video_urls.split(",") if v.strip()]
        
        if not urls_list:
            raise HTTPException(status_code=400, detail="No se proporcionaron URLs de video válidas de Pexels.")

        # 2. Descargar el archivo de audio local desde Catbox
        audio_path = os.path.join(tmp_dir, "audio.mp3")
        audio_res = requests.get(audio_url, headers=HEADERS, stream=True)
        
        if audio_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"No se pudo descargar el audio desde Catbox: {audio_res.status_code}")
        
        with open(audio_path, "wb") as f:
            for chunk in audio_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 3. Descargar cada clip de video de Pexels
        video_files = []
        for i, v_url in enumerate(urls_list):
            v_path = os.path.join(tmp_dir, f"video_{i}.mp4")
            v_res = requests.get(v_url, headers=HEADERS, stream=True)
            if v_res.status_code == 200:
                with open(v_path, "wb") as f:
                    for chunk in v_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                video_files.append(v_path)

        if not video_files:
            raise HTTPException(status_code=400, detail="No se pudo descargar ningún video de Pexels.")

        # 4. Crear archivo de lista (demuxer concat) para FFmpeg
        concat_list_path = os.path.join(tmp_dir, "concat_list.txt")
        with open(concat_list_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        # 5. Procesar con FFmpeg (Concatena videos y ajusta la duración al audio)
        output_video_path = os.path.join(tmp_dir, "output_final.mp4")
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",  # Ajusta el corte final a la duración exacta del audio de Catbox
            output_video_path
        ]
        
        process = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            error_msg = process.stderr.decode('utf-8', errors='ignore')
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {error_msg}")

        # 6. Retornar directamente el archivo binario del video resultante hacia n8n
        return FileResponse(
            output_video_path, 
            media_type="video/mp4", 
            filename="final_video.mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
