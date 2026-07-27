from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    file_path = f"videos/{identificacion}.mp4"
    
    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        return {"estado": "pendiente"}
