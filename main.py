import os
import uuid
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class VideoRequest(BaseModel):
    video_url: str
    audio_url: str

@app.post("/render")
def render_video(data: VideoRequest):
    session_id = str(uuid.uuid4())
    temp_video = f"/tmp/{session_id}_bg.mp4"
    temp_audio = f"/tmp/{session_id}_audio.mp3"
    output_video = f"/tmp/{session_id}_output.mp4"

    try:
        # Descargar Video de fondo
        res_v = requests.get(data.video_url, stream=True)
        with open(temp_video, 'wb') as f:
            for chunk in res_v.iter_content(chunk_size=8192):
                f.write(chunk)

        # Descargar Audio
        res_a = requests.get(data.audio_url, stream=True)
        with open(temp_audio, 'wb') as f:
            for chunk in res_a.iter_content(chunk_size=8192):
                f.write(chunk)

        # Unir Audio y Video con FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", temp_video,
            "-i", temp_audio,
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", output_video
        ]
        
        subprocess.run(cmd, check=True)

        return FileResponse(output_video, media_type="video/mp4", filename="final.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for path in [temp_video, temp_audio]:
            if os.path.exists(path):
                os.remove(path)