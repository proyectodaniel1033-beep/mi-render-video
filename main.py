import os
import subprocess
import tempfile
from typing import List, Union, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Video y Voz Renderer Microservice", version="1.2.0")

class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/unir-videos")
async def unir_videos(request: Request):
    try:
        body = await request.json()
        video_url = body.get("video_url")
        audio_url = body.get("audio_url")

        if not video_url or not audio_url:
            raise HTTPException(status_code=422, detail="Faltan datos de video o audio")

        v_path = "input_video.mp4"
        a_path = "input_audio.mp3"
        o_path = "output_final.mp4"

        with open(v_path, "wb") as f:
            f.write(requests.get(video_url).content)
        with open(a_path, "wb") as f:
            f.write(requests.get(audio_url).content)

        cmd = ["ffmpeg", "-y", "-i", v_path, "-i", a_path, "-c:v", "copy", "-c:a", "aac", "-shortest", o_path]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {"status": "success", "message": "Video unido correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    try:
        if not payload.text:
            raise HTTPException(status_code=400, detail="El texto para la voz está vacío.")

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_file.close()

        communicate = edge_tts.Communicate(payload.text, payload.voice)
        await communicate.save(output_file.name)

        return FileResponse(
            output_file.name, 
            media_type="audio/mpeg", 
            filename="cancion_generada.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la voz: {str(e)}")

@app.post("/render-final")
async def render_final(video: UploadFile = File(...), audio: UploadFile = File(...)):
    try:
        video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        
        video_path.write(await video.read())
        video_path.close()
        
        audio_path.write(await audio.read())
        audio_path.close()
        output_path.close()

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path.name,
            "-i", audio_path.name,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path.name
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error en FFmpeg: {result.stderr.decode('utf-8')}")

        return FileResponse(
            output_path.name,
            media_type="video/mp4",
            filename="video_final_con_audio.mp4"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno en render final: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
