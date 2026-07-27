from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    # Sin el símbolo # al inicio para que la línea funcione:
    file_path = f"{identificacion}.mp4"

    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        return {"estado": "pendiente"}
