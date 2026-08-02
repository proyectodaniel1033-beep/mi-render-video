import os
import subprocess
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos JSON"}), 400

        video_urls = data.get("video_urls", [])
        audio_url = data.get("audio_url")
        webhook_url = data.get("webhook_url")

        if not video_urls:
            return jsonify({"error": "No se encontró ninguna URL de video"}), 400

        video_url = video_urls[0]
        print(f"Descargando video desde: {video_url}")
        
        # Descarga segura del video
        video_response = requests.get(video_url, stream=True)
        if video_response.status_code != 200:
            return jsonify({"error": "No se pudo descargar el video de la fuente"}), 500

        with open("input_video.mp4", "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Descarga segura del audio
        print(f"Descargando audio desde: {audio_url}")
        audio_response = requests.get(audio_url, stream=True)
        if audio_response.status_code != 200:
            return jsonify({"error": "No se pudo descargar el audio"}), 500

        with open("input_audio.mp3", "wb") as f:
            for chunk in audio_response.iter_content(chunk_size=8192):
                f.write(chunk)

        output_video = "output_final.mp4"

        # Comando FFmpeg ultra-compatible que reescala y fuerza streams universales
        print("Procesando con FFmpeg...")
        ffmpeg_cmd = (
            "ffmpeg -y -i input_video.mp4 -i input_audio.mp3 "
            "-c:v libx264 -preset ultrafast -crf 23 "
            "-c:a aac -b:a 192k "
            "-shortest output_final.mp4"
        )

        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error crítico en FFmpeg: {result.stderr}")
            return jsonify({"error": "Error interno en FFmpeg", "details": result.stderr}), 500

        print("¡Video procesado con éxito!")

        # Notificar al Webhook de n8n (nodo Wait)
        if webhook_url:
            try:
                requests.post(webhook_url, json={"status": "completed", "video": output_video})
            except Exception as e:
                print(f"Error al notificar el webhook: {str(e)}")

        return jsonify({"status": "success", "message": "Proceso finalizado correctamente"}), 200

    except Exception as e:
        print(f"Excepción general: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
