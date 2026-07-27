from fastapi.responses import FileResponse
import os

@app.get("/download/{job_id}")
def download_video(job_id: str):
    # Ruta donde se guarda tu video renderizado
    video_path = f"/app/videos/{job_id}.mp4" 
    
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4", filename="video.mp4")
    else:
        return {"error": "El video aún no está listo o no existe"}
