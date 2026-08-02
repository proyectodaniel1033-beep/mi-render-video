import os
import subprocess
import tempfile
from typing import List
import requests
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

def download_file(url: str, dest_path: str):
    """Descarga un archivo desde una URL de forma segura."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            raise Exception(f"Error HTTP {response.status_code} al descargar desde {url}")
    except Exception as e:
        raise Exception(f"No se pudo descargar el archivo desde {url}: {str(e)}")

def upload_to_catbox(file_path: str) -> str:
    """Sube el archivo de video final de vuelta a Catbox."""
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
    audio_url: str = Form(...),  # Recibe el enlace de Catbox para el audio
    video_urls: str = Form(...)  # Recibe la lista de enlaces de Pexels separados por comas
):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Descargar el archivo de audio de Catbox
            audio_path = os.path.join(temp_dir, "audio.mp3")
            download_file(audio_url.strip(), audio_path)
            
            # 2. Separar los enlaces de los videos de Pexels por comas y descargarlos en automático
            lista_urls = [url.strip() for url in video_urls.split(",") if url.strip()]
            
            if not lista_urls:
                return JSONResponse(status_code=400, content={"error": "No se recibieron URLs de video válidas."})
            
            video_files = []
            for i, url in enumerate(lista_urls):
                video_path = os.path.join(temp_dir, f"video_{i}.mp4")
                download_file(url, video_path)
                video_files.append(video_path)
            
            # 3. Crear el archivo de lista para FFmpeg (concatenación de clips)
            list_file_path = os.path.join(temp_dir, "file_list.txt")
            with open(list_file_path, "w") as f:
                for v_path in video_files:
                    # FFmpeg requiere escapar las rutas correctamente
                    f.write(f"file '{v_path}'\n")
            
            concatenated_path = os.path.join(temp_dir, "concatenated.mp4")
            
            # 4. Unir los clips de video usando FFmpeg
            concat_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", list_file_path, "-c", "copy", concatenated_path
            ]
            subprocess.run(concat_cmd, check=True)
            
            # 5. Combinar el video unido con el audio de Catbox
            output_path = os.path.join(temp_dir, "output_final.mp4")
            final_cmd = [
                "ffmpeg", "-y", "-i", concatenated_path, "-i", audio_path,
                "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
                "-shortest", output_path
            ]
            subprocess.run(final_cmd, check=True)
            
            # 6. Subir el resultado final de regreso a Catbox (o el servicio configurado) para n8n
            final_url = upload_to_catbox(output_path)
            
            return {"enlace_video_final": final_url}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
