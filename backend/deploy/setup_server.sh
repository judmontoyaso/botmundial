#!/bin/bash
# Run this ONCE on the VPS as root or with sudo.
# Clona el repo, crea el venv, configura systemd y abre el puerto.
#
# Usage:
#   ssh user@your-server
#   curl -sSL https://raw.githubusercontent.com/judmontoyaso/botmundial/main/backend/deploy/setup_server.sh | bash
#   # or copy the file and run: bash setup_server.sh

set -e

REPO_URL="https://github.com/judmontoyaso/botmundial.git"
INSTALL_DIR="/opt/botmundial"
SERVICE_USER="promundial"
PYTHON_MIN="3.10"

echo "=== ProMundial API — Server Setup ==="

# 1. System packages
apt-get update -q
apt-get install -y -q python3 python3-pip python3-venv git nginx

# 2. Dedicated system user (no login shell)
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
    echo "Created user: $SERVICE_USER"
fi

# 3. Clone repo
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repo already cloned — pulling latest..."
    git -C "$INSTALL_DIR" pull origin main
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"

# 4. Python venv
cd "$INSTALL_DIR/backend"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet
echo "Dependencies installed."

# 5. .env file — prompt if missing
ENV_FILE="$INSTALL_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo ">>> Create $ENV_FILE with your credentials <<<"
    cat > "$ENV_FILE" <<'ENVTEMPLATE'
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_MODEL=deepseek-v4-pro
FRONTEND_URL=https://your-frontend.vercel.app
ENVTEMPLATE
    echo "Template written to $ENV_FILE — EDIT IT before starting the service."
fi

# 6. Systemd service
cp "$INSTALL_DIR/backend/deploy/promundial-api.service" /etc/systemd/system/promundial-api.service
systemctl daemon-reload
systemctl enable promundial-api
echo "Systemd service registered."

# 7. Nginx reverse proxy (port 80 → 8000)
cat > /etc/nginx/sites-available/promundial <<'NGINX'
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/promundial /etc/nginx/sites-enabled/promundial
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
echo "Nginx configured."

# 8. Allow sudo systemctl restart without password (for deploy user)
SUDOERS_LINE="$SERVICE_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart promundial-api, /bin/systemctl is-active promundial-api"
if ! grep -qF "promundial-api" /etc/sudoers.d/promundial 2>/dev/null; then
    echo "$SUDOERS_LINE" > /etc/sudoers.d/promundial
    chmod 440 /etc/sudoers.d/promundial
fi

echo ""
echo "=== Setup complete ==="
echo "Next steps:"
echo "  1. Edit $ENV_FILE with your real credentials"
echo "  2. sudo systemctl start promundial-api"
echo "  3. sudo systemctl status promundial-api"
echo "  4. Add GitHub Secrets (see README or deploy/setup_server.sh comments)"
echo ""
echo "GitHub Secrets needed:"
echo "  DEPLOY_HOST  = $(curl -s ifconfig.me)"
echo "  DEPLOY_USER  = $SERVICE_USER  (or your SSH user)"
echo "  DEPLOY_KEY   = contents of your private SSH key"
echo "  DEPLOY_PORT  = 22"
