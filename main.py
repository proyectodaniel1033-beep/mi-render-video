import os
import subprocess
import requests
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    # 1. Verificar que llegue el audio local de la IA
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    input_audio = "input_audio.mp3"
    audio_file.save(input_audio)

    # 2. Recibir las URLs de los videos de stock enviadas por n8n (desde el Aggregate)
    video_urls_raw = request.form.get("video_urls", "[]")
    webhook_url = request.form.get("webhook_url")

    try:
        video_urls = json.loads(video_urls_raw)
    except:
        video_urls = [video_urls_raw] if video_urls_raw else []

    if not video_urls:
        return jsonify({"error": "Missing video_urls"}), 400

    output_video = "output_final.mp4"

    try:
        # 3. Descargar cada uno de los clips de video cortos
        video_files = []
        for i, url in enumerate(video_urls):
            v_name = f"video_part_{i}.mp4"
            try:
                vid_res = requests.get(url, stream=True, timeout=15)
                if vid_res.status_code == 200:
                    with open(v_name, "wb") as f:
                        for chunk in vid_res.iter_content(chunk_size=8192):
                            f.write(chunk)
                    video_files.append(v_name)
            except Exception as e:
                print(f"No se pudo descargar el video {i}: {str(e)}")

        if not video_files:
            return jsonify({"error": "Failed to download any video parts"}), 400

        # 4. Crear archivo de lista para FFmpeg con bucle integrado
        # Repetimos la secuencia de clips varias veces (ej. 5 veces) para asegurar que superen los 2 minutos
        list_filename = "file_list.txt"
        with open(list_filename, "w") as f:
            for _ in range(5): 
                for v_name in video_files:
                    f.write(f"file '{v_name}'\n")

        # 5. Unir los videos en un video base continuo
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

        # 6. Sincronizar el video largo con tu audio local y forzar el corte exacto con -shortest
        final_command = [
            "ffmpeg", "-y",
            "-i", combined_video,
            "-i", input_audio,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",  # Corta de forma estricta justo al terminar tu audio local
            "-pix_fmt", "yuv420p",
            output_video
        ]
        
        result = subprocess.run(final_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Error FFmpeg: {result.stderr}")
            return jsonify({"error": "FFmpeg failed", "details": result.stderr}), 500

        print("¡Video largo generado y sincronizado con éxito!")

        # 7. Subir el resultado final a Catbox
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
                    print(f"Subido a Catbox: {downloaded_url}")
        except Exception as e:
            print(f"Error al subir: {str(e)}")

        # 8. Notificar a n8n si hay webhook
        if webhook_url:
            try:
                requests.post(webhook_url, json={"status": "completed", "video": downloaded_url})
            except:
                pass

        return jsonify({"status": "success", "video_url": downloaded_url}), 200

    except Exception as e:
        print(f"Error general: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
