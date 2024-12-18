# Usar la imagen base de Python 3.10 slim para un entorno más ligero
FROM python:3.10-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Instalar cmake, herramientas de compilación y dependencias de PostgreSQL
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de dependencias
COPY requirements.txt /app/

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . /app/

RUN python manage.py migrate
# Exponer el puerto que usará Django
EXPOSE 8000

# Comando para iniciar el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
