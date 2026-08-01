import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/transcode', methods=['POST'])
def transcode():
    data = request.json
    # Ahora esperamos una lista de videos en lugar de uno solo
    video_urls = data.get('video_urls', [])
    audio_url = data.get('audio_url')
    
    if not video_urls:
        return jsonify({"error": "No se proporcionaron URLs de video"}), 400

    downloaded_files = []
    
    # 1. Descargar cada video de la lista de forma temporal
    for i, url in enumerate(video_urls):
        local_video = f"input_{i}.mp4"
        os.system(f"curl -L '{url}' -o {local_video}")
        downloaded_files.append(local_video)

    # 2. Crear un archivo de texto que FFmpeg necesita para unir los videos (Concat demuxer)
    with open("mylist.txt", "w") as f:
        for file in downloaded_files:
            f.write(f"file '{file}'\n")

    # 3. Unir los videos y añadir el audio con FFmpeg
    output_video = "output_final.mp4"
    
    # Comando FFmpeg para concatenar videos y mezclar el audio
    ffmpeg_cmd = (
        f"ffmpeg -f concat -safe 0 -i mylist.txt -i {audio_url} "
        f"-c:v libx264 -c:a aac -map 0:v:0 -map 1:a:0 -shortest {output_video} -y"
    )
    
    subprocess.run(ffmpeg_cmd, shell=True)

    # Aquí retornarías o subirías tu video resultante
    return jsonify({"status": "success", "message": "Video combinado y procesado correctamente"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
