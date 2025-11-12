FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# Instala dependencias de forma reproducible; cae a npm install si falla ci (entornos locales)
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund
COPY . .
# Permite inyectar la URL del backend en build (Railway → Build Args)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM node:20-alpine
WORKDIR /app
RUN npm i -g serve
COPY --from=build /app/dist ./dist
EXPOSE 3000
# Respeta ${PORT} provisto por Railway
CMD ["sh","-lc","serve -s dist -l ${PORT:-3000}"]