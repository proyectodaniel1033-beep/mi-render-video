import os
import subprocess
import tempfile
from typing import List, Union, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Video y Voz Renderer Microservice", version="1.1.0")

class VideoRequest(BaseModel):
    urls: Union[List[Any], dict, str, None] = None

class VoiceRequest(BaseModel):
    text: str
    voice: str = "es-MX-DaliaNeural"

@app.post("/unir-videos")
async def unir_videos(payload: VideoRequest):
    try:
        raw_data = payload.urls
        urls_limpias = []

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

        if not urls_limpias:
            raise HTTPException(status_code=400, detail="La lista de URLs está vacía o el formato no es válido.")

        return {
            "status": "success",
            "message": "Videos procesados correctamente",
            "total_urls": len(urls_limpias),
            "urls": urls_limpias
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/generar-voz")
async def generar_voz(payload: VoiceRequest):
    try:
        if not payload.text:
            raise HTTPException(status_code=400, detail="El texto para la voz está vacío.")

        # Crear archivo temporal para el audio (.mp3)
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        output_file.close()

        # Generar audio con edge-tts (Gratis y con voces neuronales de alta calidad)
        communicate = edge_tts.Communicate(payload.text, payload.voice)
        await communicate.save(output_file.name)

        return FileResponse(
            output_file.name, 
            media_type="audio/mpeg", 
            filename="cancion_generada.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar la voz: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
