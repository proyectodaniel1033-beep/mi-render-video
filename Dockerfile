# Usamos una imagen oficial de Python ligera
FROM python:3.10-slim

# Instalamos ffmpeg y dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos e instalamos los requerimientos de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Render asigna dinámicamente un puerto mediante la variable de entorno PORT.
# Usamos sh para permitir que uvicorn lea la variable $PORT correctamente.
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"
