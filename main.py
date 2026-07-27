from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    # Ruta absoluta o relativa donde tu script guarda el video renderizado
    # Si se guarda en la carpeta principal, déjalo así:
    file_path = f"{identificacion}.mp4"
    
    # Si tu script lo guarda dentro de una carpeta llamada 'videos', usa esta línea en su lugar:
    # file_path = f"videos/{identificacion}.mp4"

    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        return {"estado": "pendiente"}
