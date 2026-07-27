from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
import subprocess
import os

app = FastAPI()

def procesar_video_con_ffmepg(identificacion: str):
    output_file = f"{identificacion}.mp4"
    
    comando = [
        "ffmpeg",
        "-stream_loop", "9",
        "-i", "entrada.mp4",
        "-t", "120",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_file
    ]
    
    subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.post("/renderizar/{identificacion}")
async def iniciar_renderizado(identificacion: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(procesar_video_con_ffmepg, identificacion)
    return {"mensaje": "Proceso iniciado", "identificacion": identificacion}

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    file_path = f"{identificacion}.mp4"
    
    if os.path.exists(file_path):
        return {
            "estado": "completado",
            "url": f"https://mi-render-video.onrender.com/{file_path}"
        }
    else:
        return {"estado": "pendiente"}

@app.get("/download/{identificacion}")
async def descargar_video(identificacion: str):
    file_path = f"{identificacion}.mp4"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=file_path)
    return {"error": "El archivo aún no está listo o no existe"}
