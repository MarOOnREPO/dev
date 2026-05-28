# 🎬 Torrent Stream Player

> **Browser-based video player** that streams torrents/magnet links with support for **x265 HEVC**, **AC3 audio**, **multiple audio tracks**, and **subtitles** — optimized for both **laptop and mobile browsers**.

[![Node.js](https://img.shields.io/badge/Node.js-22+-green)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-required-orange)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Deployment](#-deployment)
  - [Docker (Recommended)](#docker-recommended)
  - [VPS Bare Metal](#vps-bare-metal-linode-lightsail)
  - [SSL with Let's Encrypt](#ssl-with-lets-encrypt)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [Troubleshooting](#-troubleshooting)
- [Security](#-security)

---

## ✨ Features

| Feature | Status | Notes |
|---|---|---|
| **x265/HEVC Source** | ✅ | Transcoded to H.264 for browser compatibility |
| **AC3 Source** | ✅ | Transcoded to AAC for universal playback |
| **Multiple Audio Tracks** | ✅ | Auto-detected + selectable in player |
| **Subtitles (SRT/ASS/VTT)** | ✅ | Extracted & converted to WebVTT |
| **Magnet Links** | ✅ | Full WebTorrent support |
| **Laptop Browser** | ✅ | Chrome, Firefox, Safari, Edge |
| **Mobile Browser** | ✅ | iOS Safari, Android Chrome |
| **PWA** | ✅ | Installable app with offline assets |
| **HLS Streaming** | ✅ | Adaptive streaming via hls.js / native |
| **Rate Limiting** | ✅ | API abuse protection |
| **Structured Logging** | ✅ | Pino JSON logs |
| **Health Checks** | ✅ | `/api/health` endpoint |

---

## 🏗 Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Browser       │────▶│  Node.js Server  │────▶│   WebTorrent    │
│  (Laptop/Mobile)│◀────│  Express + Pino  │◀────│  (P2P Download) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         ▲                        │
         │                        ▼
         │               ┌──────────────────┐
         └───────────────│     FFmpeg       │
                         │ x265/AC3 ──▶ HLS │
                         │ H.264/AAC/VTT    │
                         └──────────────────┘
```

### Why Transcoding?

Browsers **cannot** natively decode x265/HEVC or AC3 due to licensing/patent restrictions. The server transcodes on-the-fly to:
- **H.264 Baseline** — universally supported
- **AAC** — universal audio
- **HLS (.m3u8)** — streaming protocol supported by all browsers

---

## 🚀 Quick Start

### Prerequisites
- Node.js 22+
- FFmpeg 6+
- npm or yarn

### Local Development

```bash
# Clone
git clone https://github.com/MarOOnREPO/torrent-stream-player.git
cd torrent-stream-player

# Install backend dependencies
cd backend && npm install && cd ..

# Start server
cd backend && node server.js

# Open in browser
# http://localhost:3000
```

### Docker (One Command)

```bash
docker-compose up --build -d
```

Access at `http://localhost:3000`

---

## 🖥 Deployment

### Docker (Recommended)

```bash
# Clone on your VPS
git clone https://github.com/MarOOnREPO/torrent-stream-player.git
cd torrent-stream-player

# Update domain in docker-compose.yml and deployment/nginx.conf
# Replace "your-domain.com" with your actual domain

# Start everything
docker-compose up --build -d

# Get SSL certificate
docker-compose exec certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d your-domain.com --agree-tos --email admin@your-domain.com
```

### VPS Bare Metal (Linode Lightsail)

#### Recommended VPS Specs

| Component | Minimum | Recommended |
|---|---|---|
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 2 GB | 4 GB |
| **Storage** | 20 GB SSD | 50 GB SSD |
| **Bandwidth** | 2 TB | 5 TB |
| **OS** | Ubuntu 24.04 LTS | Ubuntu 24.04 LTS |

> ⚠️ **FFmpeg transcoding is CPU-intensive.** For 1080p x265 content, a 4 vCPU instance is strongly recommended. Consider adding swap if using 2 GB RAM.

#### Step-by-Step Deployment

**Step 1: Create Linode Instance**

1. Log in to [Linode Cloud Manager](https://cloud.linode.com/)
2. Click **Create** → **Linode**
3. Choose **Ubuntu 24.04 LTS**
4. Select **Dedicated 4GB** (2 vCPU, 4 GB RAM) or higher
5. Choose a data center region close to your users
6. Set root password and click **Create Linode**
7. Wait for provisioning (~2 minutes)
8. Note the **Public IP Address**

**Step 2: DNS Setup**

Point your domain to the Linode IP:
```
Type: A
Name: @ (or player)
Value: YOUR_LINODE_IP
TTL: 300
```

**Step 3: Connect & Deploy**

```bash
# SSH into your VPS
ssh root@YOUR_LINODE_IP

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y curl git ffmpeg nginx certbot python3-certbot-nginx

# Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# Create app user
useradd -r -s /bin/false -m -d /home/torrentplayer torrentplayer

# Clone project
mkdir -p /opt && cd /opt
git clone https://github.com/MarOOnREPO/torrent-stream-player.git
cd torrent-stream-player

# Install backend dependencies
cd backend
npm ci --only=production
cd ..

# Create directories
mkdir -p downloads logs
chown -R torrentplayer:torrentplayer /opt/torrent-stream-player

# Configure Nginx
cp deployment/nginx.conf /etc/nginx/nginx.conf
sed -i 's/your-domain.com/player.yourdomain.com/g' /etc/nginx/nginx.conf
nginx -t && systemctl restart nginx

# Get SSL certificate
certbot --nginx -d player.yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com

# Setup systemd service
cp deployment/torrent-player.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable torrent-player
systemctl start torrent-player

# Configure firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Verify
curl http://localhost:3000/api/health
```

**Step 4: Verify Deployment**

```bash
# Check service status
systemctl status torrent-player

# View logs
journalctl -u torrent-player -f

# Check health endpoint
curl https://player.yourdomain.com/api/health
```

### SSL with Let's Encrypt

```bash
# Initial certificate
certbot --nginx -d your-domain.com

# Auto-renewal (usually already set up by certbot)
certbot renew --dry-run

# Force renew
certbot renew --force-renewal
```

---

## 📡 API Reference

### `POST /api/torrents`
Add a torrent from magnet link.

**Request:**
```json
{
  "magnetUri": "magnet:?xt=urn:btih:..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "metadata",
  "message": "Torrent added"
}
```

### `GET /api/torrents/:id`
Get torrent status, audio tracks, and subtitles.

**Response:**
```json
{
  "id": "uuid",
  "status": "ready",
  "progress": 100,
  "transcodeProgress": 100,
  "info": { "name": "Movie.mkv", ... },
  "probe": {
    "audioTracks": [
      { "index": 0, "codec": "ac3", "language": "eng", "title": "English", "channels": 6 }
    ],
    "subtitleStreams": [
      { "index": 0, "codec": "subrip", "language": "fre", "title": "French" }
    ]
  },
  "extractedSubtitles": [
    { "name": "subs.srt", "language": "subs" }
  ]
}
```

### `GET /api/stream/:id/playlist.m3u8`
HLS master playlist.

### `GET /api/stream/:id/segment_001.ts`
HLS video segment.

### `GET /api/subs/:id/filename.srt`
Subtitle file (served as WebVTT).

### `GET /api/health`
Health check endpoint.

```json
{
  "status": "ok",
  "uptime": 3600,
  "torrents": 2,
  "memory": { "rss": 95346688, ... },
  "timestamp": "2026-05-28T21:19:39.236Z"
}
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NODE_ENV` | `development` | Environment mode |
| `PORT` | `3000` | Server port |
| `LOG_LEVEL` | `info` | Pino log level (trace/debug/info/warn/error) |
| `DOWNLOADS_DIR` | `./downloads` | Torrent download directory |
| `ALLOWED_ORIGINS` | `localhost:3000,localhost:5173` | CORS allowed origins (comma-separated) |

---

## 🛡 Security

- ✅ Input validation on magnet links
- ✅ Rate limiting (20 req/min on API)
- ✅ CORS restricted origins (no `*` in production)
- ✅ Non-root Docker user
- ✅ Systemd sandboxing (`ProtectSystem=strict`)
- ✅ SSL/TLS via Let's Encrypt
- ✅ Security headers (X-Frame-Options, XSS Protection, etc.)
- ✅ Structured logging with request IDs

---

## 🐛 Troubleshooting

### "No video file found in torrent"
The torrent doesn't contain a recognized video file. Supported formats: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.m4v`

### "ffmpeg error" during transcoding
Check that ffmpeg is installed and supports libx264:
```bash
ffmpeg -encoders | grep libx264
```

### High CPU usage
Transcoding x265 to H.264 is CPU-intensive. Options:
1. Upgrade VPS to more vCPUs
2. Use `-preset ultrafast` (lower quality, faster)
3. Pre-transcode files instead of on-the-fly

### Mobile browser won't play
- iOS: Uses native HLS (Safari supports it)
- Android Chrome: Uses hls.js
- Make sure you're serving over HTTPS (required for some mobile features)

### WebTorrent won't connect
Some networks block WebRTC/BitTorrent traffic. Try:
- Using a VPN on the server
- Adding WebTorrent trackers manually
- Using TCP-only connections

---

## 📂 Project Structure

```
torrent-stream-player/
├── backend/
│   ├── server.js              # Express + WebTorrent + FFmpeg
│   ├── package.json
│   └── package-lock.json
├── frontend/
│   ├── index.html             # Player UI
│   ├── style.css              # Dark theme, responsive
│   ├── app.js                 # Video.js + hls.js + state mgmt
│   ├── sw.js                  # Service Worker (PWA)
│   └── manifest.json          # PWA manifest
├── deployment/
│   ├── nginx.conf             # Reverse proxy + SSL
│   ├── torrent-player.service # systemd service
│   └── deploy.sh              # Automated deploy script
├── Dockerfile                 # Production container
├── docker-compose.yml         # Full stack orchestration
└── README.md                  # This file
```

---

## 📜 License

MIT — See [LICENSE](LICENSE)

---

## 🙏 Credits

Built with the help of **Multi-Harness Agentic Plugin Marketplace** agents & skills:
- `nodejs-backend-patterns` — backend architecture
- `frontend-mobile-development` — responsive/PWA design
- `backend-api-security` — security hardening
- `ship-mate__architect` — project orchestration
