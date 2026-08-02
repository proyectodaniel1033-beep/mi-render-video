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

        # 1. Descargar el primer video de la lista
        video_url = video_urls[0]
        print(f"Descargando video desde: {video_url}")
        video_response = requests.get(video_url, stream=True)
        if video_response.status_code != 200:
            return jsonify({"error": "No se pudo descargar ningún video"}), 500

        with open("input_0.mp4", "wb") as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Definir ruta del video de salida
        output_video = "output_final.mp4"

        # 3. Ejecutar FFmpeg simplificado para unir video y audio directos
        print("Iniciando procesamiento con FFmpeg...")
        ffmpeg_cmd = (
            f"ffmpeg -i input_0.mp4 -i \"{audio_url}\" "
            f"-c:v libx264 -c:a aac -shortest {output_video} -y"
        )

        result = subprocess.run(ffmpeg_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error en FFmpeg: {result.stderr}")
            return jsonify({"error": "Error en FFmpeg", "details": result.stderr}), 500

        print("Procesamiento completado con éxito.")

        # 4. Si hay webhook configurado, notificar de vuelta a n8n para liberar el nodo Wait
        if webhook_url:
            try:
                requests.post(webhook_url, json={"status": "completed", "video": output_video})
            except Exception as e:
                print(f"Error al notificar al webhook: {str(e)}")

        return jsonify({"status": "success", "message": "Video procesado correctamente"}), 200

    except Exception as e:
        print(f"Excepción interna: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
