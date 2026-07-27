from fastapi import FastAPI, BackgroundTasks
import subprocess
import os

app = FastAPI()

def procesar_video_con_ffmpeg(identificacion: str):
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
    background_tasks.add_task(procesar_video_con_ffmpeg, identificacion)
    return {"mensaje": "Proceso iniciado", "identificacion": identificacion}

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    file_path = f"{identificacion}.mp4"

    if os.path.exists(file_path):
        return {
            "estado": "completado",
            "url": f"https://proyectodaniel1033.onrender.com/{file_path}"
        }
    else:
        return {"estado": "pendiente"}
