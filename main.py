import os
import subprocess
from typing import List, Union, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Video Renderer Microservice", version="1.0.0")

class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

@app.post("/unir-videos")
async def unir_videos(payload: VideoRequest):
    try:
        raw_data = payload.urls
        urls_limpias = []

        # Aplanamiento inteligente y robusto para evitar cualquier error 422 o de formato de n8n
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, list):
                    urls_limpias.extend([str(i) for i in item if i])
                elif isinstance(item, dict):
                    for val in item.values():
                        if isinstance(val, list):
                            urls_limpias.extend([str(i) for i in val if i])
                        elif val:
                            urls_limpias.append(str(val))
                elif item:
                    urls_limpias.append(str(item))
        elif isinstance(raw_data, dict):
            for val in raw_data.values():
                if isinstance(val, list):
                    urls_limpias.extend([str(i) for i in val if i])
                elif val:
                    urls_limpias.append(str(val))
        elif isinstance(raw_data, str):
            urls_limpias.append(raw_data)

        # Validación estricta: Si la lista está vacía, lanzamos el 400 controlado que viste en n8n
        if not urls_limpias:
            raise HTTPException(status_code=400, detail="La lista de URLs está vacía o el formato no es válido.")

        print(f"URLs listas para procesamiento con FFmpeg: {urls_limpias}")

        # AQUÍ INTEGRAS TU LÓGICA DE DESCARGA Y FFmpeg
        # Ejemplo rápido de estructura para concatenar con FFmpeg:
        # 1. Descargar los videos a archivos temporales
        # 2. Crear archivo de texto de lista para ffmpeg (concat demuxer)
        # 3. Ejecutar subproceso de ffmpeg

        return {
            "status": "success",
            "message": "Videos procesados correctamente",
            "total_urls": len(urls_limpias),
            "urls": urls_limpias
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Excepción capturada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
