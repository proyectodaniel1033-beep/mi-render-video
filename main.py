from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
import subprocess
import requests
import os

app = FastAPI()

@app.post("/unir-videos")
async def unir_videos(request: Request):
    v_path = "input_video.mp4"
    a_path = "input_audio.mp3"
    o_path = "output_final.mp4"
    
    try:
        body = await request.json()
        video_url = body.get("video_url")
        audio_url = body.get("audio_url")

        if not video_url or not audio_url:
            raise HTTPException(status_code=422, detail="Faltan datos de video o audio")

        with open(v_path, "wb") as f:
            f.write(requests.get(video_url).content)
        with open(a_path, "wb") as f:
            f.write(requests.get(audio_url).content)

        cmd = ["ffmpeg", "-y", "-i", v_path, "-i", a_path, "-c:v", "copy", "-c:a", "aac", "-shortest", o_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return FileResponse(o_path, media_type="video/mp4", filename="video_final.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
