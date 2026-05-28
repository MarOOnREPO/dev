# ── Torrent Stream Player ── Production Dockerfile
# Multi-stage build: Node.js backend + static frontend

FROM node:22-slim AS builder
WORKDIR /app
COPY backend/package.json backend/package-lock.json ./backend/
RUN cd backend && npm ci --only=production

FROM node:22-slim
WORKDIR /app

# Install ffmpeg (required for transcoding x265/AC3 to H.264/AAC)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create downloads directory
RUN mkdir -p /app/downloads

# Copy backend
COPY --from=builder /app/backend/node_modules ./backend/node_modules
COPY backend/ ./backend/

# Copy frontend
COPY frontend/ ./frontend/

# Security: run as non-root
RUN groupadd -r torrentplayer && useradd -r -g torrentplayer torrentplayer
RUN chown -R torrentplayer:torrentplayer /app/downloads
USER torrentplayer

ENV NODE_ENV=production
ENV PORT=3000
ENV DOWNLOADS_DIR=/app/downloads
ENV LOG_LEVEL=info

EXPOSE 3000

WORKDIR /app/backend
CMD ["node", "server.js"]
