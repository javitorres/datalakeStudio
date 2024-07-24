# Elegir una versión específica de Python
FROM python:3.9

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos y instalar dependencias
COPY requirements.txt ./

# Actualizar e instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    ffmpeg \
    curl gzip

# Configurar variables de entorno para GDAL
ENV GDAL_CONFIG=/usr/bin/gdal-config
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto en el que se ejecuta tu aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD python ./server.py
