from fastapi import FastAPI

app = FastAPI()

@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    return {"estado": "pendiente"}
@app.get("/status/{identificacion}")
async def check_status(identificacion: str):
    # Cambia esto por la ruta real donde guardas o procesas los videos
    file_path = f"videos/{identificacion}.mp4"
    
    if os.path.exists(file_path):
        return {"estado": "completado"}
    else:
        return {"estado": "pendiente"}
