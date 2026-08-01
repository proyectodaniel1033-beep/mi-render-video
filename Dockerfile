FROM python:3.10-slim

# Instalar FFmpeg y herramientas del sistema necesarias
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

EXPOSE 10000

CMD ["python", "main.py"]
