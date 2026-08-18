from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import requests
import os

app = FastAPI()


class VideoRequest(BaseModel):
  video_url: str
  audio_url: str


@app.post("/render-final")
async def render_final(data: VideoRequest):
  video_path = "temp_video.mp4"
  audio_path = "temp_audio.mp3"
  output_path = "output_final.mp4"

  try:
    # Descargar video de Cloudinary
    video_res = requests.get(data.video_url)
    with open(video_path, "wb") as f:
      f.write(video_res.content)

    # Descargar audio desde su URL
    audio_res = requests.get(data.audio_url)
    with open(audio_path, "wb") as f:
      f.write(audio_res.content)

    # Ejecutar FFmpeg con mapeo estricto
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        output_path,
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    # Aquí devuelves o subes tu video resultante
    return {"status": "success", "message": "Video generado correctamente"}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
