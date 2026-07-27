import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/download/{identificacion}")
async def download_video(identificacion: str):
    # Asegúrate de que esta sea la ruta donde FFmpeg guarda los videos renderizados
    file_path = f"videos/{identificacion}.mp4"  # O la ruta absoluta/relativa que uses
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"No se encontró el archivo para el ID: {identificacion}")
        
    return FileResponse(file_path, media_type="video/mp4", filename="video.mp4")
