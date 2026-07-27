@app.get("/download/{identificacion}")
async def download_video(identificacion: str):
    # Tu lógica de FFmpeg para buscar el archivo generado con esa identificación
    file_path = f"/ruta/a/tu/video_{identificacion}.mp4"
    return FileResponse(file_path, media_type="video/mp4", filename="video.mp4")
