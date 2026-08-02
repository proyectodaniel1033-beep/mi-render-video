import os
import subprocess
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "message": "Microservicio FFmpeg activo"})

@app.route('/transcode', methods=['POST'])
def transcode():
    data = request.json
    
    video_urls = data.get('video_urls', [])
    audio_url = data.get('audio_url')
    webhook_url = data.get('webhook_url')

    if not video_urls:
        return jsonify({"error": "No se proporcionaron URLs de video"}), 400

    downloaded_files = []

    # 1. Descargar los videos de forma segura
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

    # 2. Crear archivo de lista para FFmpeg
    with open("mylist.txt", "w") as f:
        for file in downloaded_files:
            f.write(f"file '{file}'\n")

    # 3. Unir videos y audio con FFmpeg
    output_video = "output_final.mp4"
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i mylist.txt -i '{audio_url}' "
        f"-c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video} -y"
    )

    result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        return jsonify({"error": "Error en FFmpeg", "details": result.stderr}), 500

    # 4. Notificar obligatoriamente al webhook de n8n para liberar el nodo Wait
    if webhook_url:
        try:
            requests.post(webhook_url, json={"status": "success", "output": output_video}, timeout=10)
        except Exception as e:
            print(f"Error al notificar al webhook: {e}")

    return jsonify({"status": "success", "message": "Proceso completado con éxito"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
