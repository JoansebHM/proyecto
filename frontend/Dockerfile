# --- Etapa 1: compilar el build de React (Node 22: lo exige jsdom) ---
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- Etapa 2: servir los archivos estáticos con nginx ---
FROM nginx:1.30-alpine

# Aplica los parches de seguridad del sistema base (Trivy bloquea las vulnerabilidades críticas)
RUN apk upgrade --no-cache

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
