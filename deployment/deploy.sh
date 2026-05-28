#!/bin/bash
set -e

# ── Torrent Stream Player ── VPS Deployment Script
# Usage: ./deploy.sh your-domain.com

DOMAIN=${1:-"your-domain.com"}
APP_DIR="/opt/torrent-stream-player"
USER="torrentplayer"

echo "==================================="
echo "Torrent Stream Player Deployer"
echo "Domain: $DOMAIN"
echo "==================================="

# ── 1. System Update ──
echo "[1/8] Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

# ── 2. Install Dependencies ──
echo "[2/8] Installing dependencies..."
sudo apt-get install -y \
    curl wget git \
    ffmpeg nginx \
    certbot python3-certbot-nginx \
    docker.io docker-compose \
    build-essential

# ── 3. Create User ──
echo "[3/8] Creating service user..."
if ! id "$USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -m -d /home/$USER $USER
fi

# ── 4. Setup App Directory ──
echo "[4/8] Setting up app directory..."
sudo mkdir -p $APP_DIR
sudo cp -r ../../backend $APP_DIR/
sudo cp -r ../../frontend $APP_DIR/
sudo mkdir -p $APP_DIR/downloads $APP_DIR/logs
sudo chown -R $USER:$USER $APP_DIR

# ── 5. Install Node.js & Backend ──
echo "[5/8] Installing Node.js dependencies..."
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
cd $APP_DIR/backend
sudo -u $USER npm ci --only=production

# ── 6. Setup Nginx + SSL ──
echo "[6/8] Configuring Nginx + SSL..."
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo sed -i "s/your-domain.com/$DOMAIN/g" /etc/nginx/nginx.conf
sudo nginx -t && sudo systemctl restart nginx

# SSL
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || true

# ── 7. Setup Systemd Service ──
echo "[7/8] Creating systemd service..."
sudo cp torrent-player.service /etc/systemd/system/
sudo sed -i "s|/opt/torrent-stream-player|$APP_DIR|g" /etc/systemd/system/torrent-player.service
sudo systemctl daemon-reload
sudo systemctl enable torrent-player
sudo systemctl start torrent-player

# ── 8. Firewall ──
echo "[8/8] Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo ""
echo "==================================="
echo "✓ Deployment Complete!"
echo "==================================="
echo "App URL:    https://$DOMAIN"
echo "Health:     https://$DOMAIN/api/health"
echo "Logs:       sudo journalctl -u torrent-player -f"
echo "Status:     sudo systemctl status torrent-player"
echo ""
echo "To update: cd $APP_DIR && git pull && sudo systemctl restart torrent-player"
