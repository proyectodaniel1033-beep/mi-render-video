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

    # Ahora recibimos una lista de videos cortos
    video_urls = data.get("video_urls", [])
    audio_url = data.get("audio_url")
    webhook_url = data.get("webhook_url")

    if not video_urls or not audio_url:
        return jsonify({"error": "Missing video_urls or audio_url"}), 400

    input_audio = "input_audio.mp3"
    output_video = "output_final.mp4"

    try:
        # 1. Descargar el audio largo de la IA
        aud_res = requests.get(audio_url, stream=True)
        with open(input_audio, "wb") as f:
            for chunk in aud_res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. Descargar cada video corto y preparar la lista para concatenar
        video_files = []
        for i, url in enumerate(video_urls):
            v_name = f"video_part_{i}.mp4"
            vid_res = requests.get(url, stream=True)
            with open(v_name, "wb") as f:
                for chunk in vid_res.iter_content(chunk_size=8192):
                    f.write(chunk)
            video_files.append(v_name)

        # Crear el archivo de texto que FFmpeg usa para unir los videos en orden
        list_filename = "file_list.txt"
        with open(list_filename, "w") as f:
            for v_name in video_files:
                f.write(f"file '{v_name}'\n")

        # 3. Unir los videos en un video largo temporal
        combined_video = "combined_video.mp4"
        concat_command = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_filename,
            "-c", "copy",
            combined_video
        ]
        subprocess.run(concat_command, check=True)

        # 4. Combinar el video largo resultante con el audio de la IA y ajustar duración
        final_command = [
            "ffmpeg", "-y",
            "-i", combined_video,
            "-i", input_audio,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",  # Se detiene exactamente cuando termina el diálogo de la IA
            "-pix_fmt", "yuv420p",
            output_video
        ]
        
        result = subprocess.run(final_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error en FFmpeg final: {result.stderr}")
            return jsonify({"error": "FFmpeg failed", "details": result.stderr}), 500

        print("¡Video largo con audio generado con éxito!")

        # 5. Subir el resultado final a Catbox
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

        # 6. Notificar a n8n
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
