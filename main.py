import os
import subprocess
import tempfile
import requests
from typing import List
from fastapi import FastAPI, Form, File, UploadFile

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
    audio_url: str = Form(...),
    video_urls: List[str] = Form(...)  # Recibe múltiples URLs como una lista
):
    # Tu código para iterar sobre los videos y descargarlos:
    for i, url in enumerate(video_urls):
        video_path = os.path.join(temp_dir, f"video_{i}.mp4")
        download_file(url.strip(), video_path)
    
    # Resto de tu lógica con FFmpeg...

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
