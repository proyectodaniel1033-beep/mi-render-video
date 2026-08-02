import os
import subprocess
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    input_audio = "input_audio.mp3"
    audio_file.save(input_audio)

    # Recibimos las URLs de los videos de stock enviadas por n8n (o una lista generada automáticamente)
    video_urls_raw = request.form.get("video_urls", "[]")
    webhook_url = request.form.get("webhook_url")

    import json
    try:
        video_urls = json.loads(video_urls_raw)
    except:
        video_urls = [video_urls_raw] if video_urls_raw else []

    if not video_urls:
        return jsonify({"error": "Missing video_urls"}), 400

    output_video = "output_final.mp4"

    try:
        # 1. Descargar todos los videos cortos que n8n seleccionó automáticamente
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

        # 2. Crear archivo de lista para FFmpeg
        list_filename = "file_list.txt"
        with open(list_filename, "w") as f:
            for v_name in video_files:
                f.write(f"file '{v_name}'\n")

        # 3. Concatenar los videos para formar un video base continuo
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

        # 4. Mezclar el video continuo con el audio local y cortar exactamente donde termina el audio (-shortest)
        final_command = [
            "ffmpeg", "-y",
            "-i", combined_video,
            "-i", input_audio,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",  # Forzará a que el video final dure exactamente lo que dura tu audio local completo
            "-pix_fmt", "yuv420p",
            output_video
        ]
        
        result = subprocess.run(final_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            return jsonify({"error": "FFmpeg failed", "details": result.stderr}), 500

        # 5. Subir el resultado final a Catbox
        downloaded_url = ""
        with open(output_video, "rb") as f:
            res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload", "userhash": ""},
                files={"fileToUpload": f}
            )
            if res.status_code == 200:
                downloaded_url = res.text.strip()

        # 6. Notificar a n8n
        if webhook_url:
            try:
                requests.post(webhook_url, json={"status": "completed", "video": downloaded_url})
            except:
                pass

        return jsonify({"status": "success", "video_url": downloaded_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
