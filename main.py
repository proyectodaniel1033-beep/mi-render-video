from fastapi import FastAPI, BackgroundTasks
import subprocess
import os

app = FastAPI()

# Función en segundo plano que ejecuta FFmpeg para crear el video
def procesar_video_con_ffmpeg(identificacion: str):
    # Nombre del archivo de salida
    output_file = f"{identificacion}.mp4"
    
    # Comando de FFmpeg con tus parámetros (ajusta la entrada si usas un archivo base o URL)
    # Aquí asumimos que usas un video de entrada base llamado "entrada.mp4"
    comando = [
        "ffmpeg",
        "-stream_loop", "9",
        "-i", "entrada.mp4",
        "-t", "120",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_file
    ]
    
    # Ejecuta el comando en el servidor
    subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

@app.post("/renderizar/{identificacion}")
async def iniciar_renderizado(identificacion: str, background_tasks: BackgroundTasks):
    # Lanza FFmpeg en segundo plano para que la API responda de inmediato
    background_tasks.add_task(procesar_video_con_ffmpeg, identificacion)
    return {"mensaje": "Proceso iniciado", "identificacion": identificacion}

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    file_path = f"{identificacion}.mp4"

    # Revisa si el archivo ya se terminó de generar físicamente
    if os.path.exists(file_path):
        return {"estado": "completado", "url": f"https://tu-servicio.onrender.com/{file_path}"}
    else:
        return {"estado": "pendiente"}
