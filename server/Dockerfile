# Elegir una versión específica de Python
FROM python:3.9

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos y instalar dependencias
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del backend
COPY . .

# Exponer el puerto en el que se ejecuta tu aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["python", "./server.py"]
