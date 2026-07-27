@app.get("/status/{job_id}")
async def get_status(job_id: str):
    # Devuelve siempre un estado válido para que n8n no se detenga
    return {
        "id": job_id,
        "estado": "completado" # o "pendiente" según lo que necesites probar
    }
