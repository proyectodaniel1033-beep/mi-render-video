@app.get("/status/{job_id}")
def ver_estado(job_id: str):
    # Aquí buscas el ID en tu lista
