# syntax=docker/dockerfile:1
FROM node:20.11.0-slim  # MEDIUM FIX: Pinned version (was node:20-slim)

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY package*.json ./
RUN npm ci --omit=dev

COPY . .

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:8080/v1/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1); }).on('error', () => process.exit(1));"

CMD ["node", "app/index.js"]
