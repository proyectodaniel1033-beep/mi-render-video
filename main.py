from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    # Opción A: Si tu script guarda el video en la misma carpeta raíz o usa otra ruta, ajústala aquí.
    # Por ejemplo, si el archivo se guarda con el nombre exacto de la identificación:
    file_path = f"{identificacion}.mp4" 
    
    # O si usas una carpeta específica, asegúrate de que sea la correcta:
    # file_path = f"videos/{identificacion}.mp4"

    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        # Si el archivo aún no existe, mantenemos el estado pendiente
        return {"estado": "pendiente"}
