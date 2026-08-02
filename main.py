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
    print("--- PETICION RECIBIDA EN /transcode ---")
    
    video_urls = data.get('video_urls', [])
    audio_url = data.get('audio_url')
    webhook_url = data.get('webhook_url')

    if not video_urls:
        print("Error: No video URLs provided")
        return jsonify({"error": "No se proporcionaron URLs de video"}), 400

    downloaded_files = []

    # 1. Descarga con logs paso a paso
    for i, url in enumerate(video_urls):
        local_video = f"input_{i}.mp4"
        print(f"Descargando video {i} desde: {url}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(local_video, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded_files.append(local_video)
                print(f"Video {i} descargado con éxito.")
            else:
                print(f"Falló la descarga del video {i}, status: {response.status_code}")
        except Exception as e:
            print(f"Excepción descargando el video {i}: {e}")

    if not downloaded_files:
        print("Error: Ningún video pudo ser descargado.")
        return jsonify({"error": "No se pudo descargar ningún video"}), 500

    # 2. Crear archivo de lista
    with open("mylist.txt", "w") as f:
        for file in downloaded_files:
            f.write(f"file '{file}'\n")

    # 3. Ejecutar FFmpeg
    print("Iniciando procesamiento con FFmpeg...")
    output_video = "output_final.mp4"
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i mylist.txt -i '{audio_url}' "
        f"-c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video} -y"
    )

    result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error en FFmpeg: {result.stderr}")
        return jsonify({"error": "Error en FFmpeg", "details": result.stderr}), 500

    print("FFmpeg finalizado con éxito. Notificando al webhook de n8n...")

    # 4. Notificar a n8n
    if webhook_url:
        try:
            res_hook = requests.post(webhook_url, json={"status": "success", "output": output_video}, timeout=10)
            print(f"Webhook notificado correctamente. Status: {res_hook.status_code}")
        except Exception as e:
            print(f"Error al notificar al webhook: {e}")

    return jsonify({"status": "success", "message": "Proceso completado con éxito"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
