FROM node:18-alpine

WORKDIR /app

# Copy dependency files first (layer cache)
COPY package.json package-lock.json ./

# Install dependencies (sqlite3 needs build tools)
RUN apk add --no-cache python3 make g++ && \
    npm ci --production && \
    apk del python3 make g++

# Copy application code
COPY . .

# Drop to non-root
RUN adduser -D -h /app vuln && \
    chown -R vuln:vuln /app
USER vuln

EXPOSE 5017

HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -qO- http://localhost:5017/api/health || exit 1

CMD ["node", "app.js"]
