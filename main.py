from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    # Asegúrate de que esta línea esté descomentada y apunte exactamente a donde se crea el archivo
    file_path = f"{identificacion}.mp4"

    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        return {"estado": "pendiente"}
