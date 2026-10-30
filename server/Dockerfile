# Elegir una versión específica de Python
# Python >= 3.11 es necesario para duckdb >= 2.0 (y coincide con el venv local, ver .python-version).
# La variante slim basta: todas las dependencias se instalan como wheels precompilados.
FROM python:3.12-slim

# Establecer el directorio de trabajo
WORKDIR /app

# ffmpeg lo usa pydub para convertir el audio del asistente de voz
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requisitos y instalar dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Usuario sin privilegios, con el uid del usuario del host para que los ficheros que crea en el
# volumen de datos no queden a nombre de root (docker build --build-arg UID=$(id -u) si no es 1000)
ARG UID=1000
RUN useradd --create-home --uid $UID app && chown app:app /app
USER app
ENV HOME=/home/app

# Extensiones DuckDB dentro de la imagen: el contenedor no las descarga al arrancar y funciona sin red
RUN python -c "import duckdb; con = duckdb.connect(); [con.execute('INSTALL ' + e) for e in ('httpfs', 'spatial', 'aws', 'icu')]; con.execute('INSTALL h3 FROM community')"

# Copiar el resto del código del backend
COPY --chown=app:app . .

# Exponer el puerto en el que se ejecuta tu aplicación
EXPOSE 8000

# Forma exec: las señales de docker stop llegan a Python y el servidor se para limpiamente
CMD ["python", "server.py"]
