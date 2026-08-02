import os
import subprocess
import tempfile
import requests
from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse

app = FastAPI()

def download_file(url: str, dest_path: str):
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(dest_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        raise Exception(f"No se pudo descargar el archivo desde {url}")

def upload_to_catbox(file_path: str) -> str:
    url = "https://catbox.moe/user/api.php"
    with open(file_path, "rb") as f:
        files = {"fileToUpload": f}
        data = {"reqtype": "fileupload"}
        response = requests.post(url, data=data, files=files)
    if response.status_code == 200:
        return response.text.strip()
    raise Exception(f"Error al subir el video final: {response.text}")

@app.post("/transcode")
async def transcode_video(
    audio_url: str = Form(...),   # URL del audio alojado en Catbox
    video_urls: str = Form(...)   # URLs de los videos de Pexels
):
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Descargar el archivo de audio de Catbox
        audio_path = os.path.join(temp_dir, "audio.mp3")
        download_file(audio_url.strip(), audio_path)

        # 2. Calcular la duración exacta del audio con ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path
        ]
        try:
            duration_str = subprocess.check_output(probe_cmd).decode("utf-8").strip()
            audio_duration = float(duration_str)
        except Exception:
            audio_duration = 120.0

        # 3. Descargar los clips de video de Pexels
        urls = [u.strip().strip('"\'') for u in video_urls.replace("[", "").replace("]", "").split(",") if u.strip()]
        
        video_files = []
        for i, url in enumerate(urls):
            v_path = os.path.join(temp_dir, f"pexels_{i}.mp4")
            try:
                download_file(url, v_path)
                video_files.append(v_path)
            except Exception:
                continue

        if not video_files:
            return JSONResponse(status_code=400, content={"error": "No se descargaron clips de video"})

        # 4. Concatenar los clips de Pexels
        list_file_path = os.path.join(temp_dir, "file_list.txt")
        with open(list_file_path, "w") as f:
            for v_path in video_files:
                f.write(f"file '{v_path}'\n")

        concatenated_path = os.path.join(temp_dir, "concatenated.mp4")
        concat_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file_path, "-c", "copy", concatenated_path
        ]
        subprocess.run(concat_cmd, check=True)

        # 5. Renderizado final: Bucle de video sincronizado a la duración exacta del audio
        output_video_path = os.path.join(temp_dir, "output_final.mp4")
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", concatenated_path,
            "-i", audio_path,
            "-t", str(audio_duration),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            output_video_path
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # 6. Subir el resultado y retornar JSON limpio
        final_url = upload_to_catbox(output_video_path)
        return {"status": "success", "video_url": final_url}
