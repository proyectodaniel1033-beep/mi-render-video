from fastapi import FastAPI

app = FastAPI()

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return {
        "id": job_id,
        "estado": "completado"
    }
