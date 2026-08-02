import os
import subprocess
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    data = request.json
    
    # 1. Obtenemos la lista de varios videos, el audio y el webhook enviados desde n8n
    video_urls = data.get('video_urls', [])
    audio_url = data.get('audio_url')
    webhook_url = data.get('webhook_url')

    if not video_urls:
        return jsonify({"error": "No se proporcionaron URLs de video"}), 400

    downloaded_files = []

    # 2. Descargar cada video de la lista de forma segura usando requests
    for i, url in enumerate(video_urls):
        local_video = f"input_{i}.mp4"
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(local_video, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(local_video)
        except Exception as e:
            print(f"Error descargando el video {i}: {e}")

    if not downloaded_files:
        return jsonify({"error": "No se pudo descargar ningún video"}), 500

    # 3. Crear el archivo de texto (mylist.txt) para que FFmpeg una todos los videos en orden
    with open("mylist.txt", "w") as f:
        for file in downloaded_files:
            f.write(f"file '{file}'\n")

    # 4. Unir los videos y añadir el audio con FFmpeg
    # -shortest hace que el video final termine cuando acabe el audio o cumpla la duración requerida
    output_video = "output_final.mp4"
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i mylist.txt -i '{audio_url}' "
        f"-c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video} -y"
    )

    result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        return jsonify({"error": "Error en FFmpeg", "details": result.stderr}), 500

    # 5. Si n8n mandó un webhook, le devolvemos la respuesta de éxito
    if webhook_url:
        try:
            requests.post(webhook_url, json={"status": "success", "output": output_video})
        except Exception as e:
            print(f"Error al notificar al webhook: {e}")

    return jsonify({"status": "success", "message": "Videos combinados y procesados correctamente"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
