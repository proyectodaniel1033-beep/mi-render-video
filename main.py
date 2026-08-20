import os
import subprocess
import tempfile
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="Video Renderer Pro", version="2.0.0")

@app.post("/unir-binarios")
async def unir_binarios(files: List[UploadFile] = File(...)):
    # Carpeta temporal para los clips
    temp_dir = tempfile.mkdtemp()
    list_file_path = os.path.join(temp_dir, "list.txt")
    output_video = os.path.join(temp_dir, "final.mp4")
    
    try:
        # Guardar cada archivo recibido
        with open(list_file_path, "w") as f:
            for i, file in enumerate(files):
                file_path = os.path.join(temp_dir, f"{i}.mp4")
                with open(file_path, "wb") as buffer:
                    buffer.write(await file.read())
                # Normalizar a 720p para asegurar compatibilidad
                norm_path = os.path.join(temp_dir, f"norm_{i}.mp4")
                cmd_norm = ["ffmpeg", "-y", "-i", file_path, "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", "-r", "30", "-c:v", "libx264", "-crf", "23", "-an", norm_path]
                subprocess.run(cmd_norm, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                f.write(f"file '{norm_path}'\n")

        # Concatenar
        cmd_concat = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", output_video]
        subprocess.run(cmd_concat, check=True)

        return FileResponse(output_video, media_type="video/mp4", filename="video_largo_unido.mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
