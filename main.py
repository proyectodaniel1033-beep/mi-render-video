import os
import subprocess
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    video_urls = data.get("video_urls", [])
    audio_url = data.get("audio_url")
    webhook_url = data.get("webhook_url")

    if not video_urls or not audio_url:
        return jsonify({"error": "Missing video_urls or audio_url"}), 400

    input_video = "input_video.mp4"
    input_audio = "input_audio.mp3"
    output_video = "output_final.mp4"

    try:
        # Descargar video de entrada
        vid_res = requests.get(video_urls[0], stream=True)
        with open(input_video, "wb") as f:
            for chunk in vid_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # Descargar audio de entrada
        aud_res = requests.get(audio_url, stream=True)
        with open(input_audio, "wb") as f:
            for chunk in aud_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # Procesar con FFmpeg (unir video y audio)
        command = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-i", input_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_video
        ]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error en FFmpeg: {result.stderr}")
            return jsonify({"error": "FFmpeg failed", "details": result.stderr}), 500

        print("¡Video procesado con éxito!")

        # Subir el video resultante a Catbox para obtener un enlace público descargable
        downloaded_url = ""
        try:
            with open(output_video, "rb") as f:
                res = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload", "userhash": ""},
                    files={"fileToUpload": f}
                )
                if res.status_code == 200:
                    downloaded_url = res.text.strip()
                    print(f"Video subido correctamente: {downloaded_url}")
        except Exception as e:
            print(f"Error al subir el video: {str(e)}")

        # Notificar al Webhook de n8n con el enlace real
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    "status": "completed", 
                    "video": downloaded_url
                })
            except Exception as e:
                print(f"Error al notificar el webhook: {str(e)}")

        return jsonify({"status": "success", "video_url": downloaded_url}), 200

    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
