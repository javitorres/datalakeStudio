# Elegir una versión de Node.js
FROM node:14

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar 'package.json' y 'package-lock.json' (si está disponible)
COPY package*.json ./

# Instalar dependencias del proyecto
RUN npm install
RUN npm install codemirror

# Copiar los archivos del proyecto
COPY . .

# Construir la aplicación para producción
RUN npm run build

# Instalar un servidor HTTP simple para servir contenido estático
RUN npm install -g http-server

# Exponer el puerto para el servidor HTTP
EXPOSE 8080

# Ejecutar el servidor HTTP para servir la aplicación construida
CMD [ "http-server", "dist" ]
