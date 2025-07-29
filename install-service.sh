#!/bin/bash

# Turnstile API System Service Installation Script for Ubuntu
# Run with: sudo bash install-service.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="turnstile-api"
SERVICE_USER="turnstile"
SERVICE_GROUP="turnstile"
INSTALL_DIR="/opt/turnstile-solver"
CURRENT_DIR=$(pwd)

echo -e "${BLUE}🚀 Installing Turnstile API System Service${NC}"
echo "================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Create service user and group
echo -e "${YELLOW}👤 Creating service user and group...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --home-dir $INSTALL_DIR --shell /bin/bash --create-home $SERVICE_USER
    echo -e "${GREEN}✅ User '$SERVICE_USER' created${NC}"
else
    echo -e "${BLUE}ℹ️  User '$SERVICE_USER' already exists${NC}"
fi

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt update

# Install system dependencies
echo -e "${YELLOW}🔧 Installing system dependencies...${NC}"
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    gnupg \
    ca-certificates \
    software-properties-common

# Install Google Chrome
echo -e "${YELLOW}🌐 Installing Google Chrome...${NC}"
if ! command -v google-chrome &> /dev/null; then
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google.list
    apt update
    apt install -y google-chrome-stable
    echo -e "${GREEN}✅ Google Chrome installed${NC}"
else
    echo -e "${BLUE}ℹ️  Google Chrome already installed${NC}"
fi

# Create application directory
echo -e "${YELLOW}📁 Setting up application directory...${NC}"
mkdir -p $INSTALL_DIR
cp -r * $INSTALL_DIR/
chown -R $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR

# Create Python virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
cd $INSTALL_DIR
sudo -u $SERVICE_USER python3 -m venv venv
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}📚 Installing Python dependencies...${NC}"
sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/pip install -r requirements.txt

# Setup environment file
echo -e "${YELLOW}⚙️  Setting up environment configuration...${NC}"
if [ ! -f "$INSTALL_DIR/.env" ]; then
    # Generate secure API key
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    cat > $INSTALL_DIR/.env << EOF
# Turnstile API Production Configuration

# Security - GENERATED SECURE API KEY
TURNSTILE_API_KEY=$API_KEY

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Browser Settings
HEADLESS=true
BROWSER_TYPE=chromium
THREADS=2
USER_AGENT=

# Performance Settings
WORKERS=1
MAX_CONNECTIONS=100
EOF

    chown $SERVICE_USER:$SERVICE_GROUP $INSTALL_DIR/.env
    chmod 600 $INSTALL_DIR/.env  # Secure permissions for API key
    
    echo -e "${GREEN}✅ Environment file created with secure API key${NC}"
    echo -e "${YELLOW}🔑 Generated API Key: ${API_KEY}${NC}"
    echo -e "${YELLOW}⚠️  Save this API key - you'll need it for requests!${NC}"
else
    echo -e "${BLUE}ℹ️  Environment file already exists${NC}"
fi

# Install systemd service
echo -e "${YELLOW}🛠️  Installing systemd service...${NC}"
cp $CURRENT_DIR/turnstile-api.service /etc/systemd/system/
systemctl daemon-reload

# Enable and start service
echo -e "${YELLOW}🚀 Enabling and starting service...${NC}"
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Wait a moment for service to start
sleep 3

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Service started successfully!${NC}"
    systemctl status $SERVICE_NAME --no-pager -l
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo -e "${YELLOW}📋 Service logs:${NC}"
    journalctl -u $SERVICE_NAME --no-pager -l
    exit 1
fi

# Setup firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
    ufw allow 8000/tcp comment "Turnstile API"
    echo -e "${GREEN}✅ Firewall configured${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
echo "================================="
echo -e "${BLUE}📊 Service Information:${NC}"
echo "• Service name: $SERVICE_NAME"
echo "• Install directory: $INSTALL_DIR"
echo "• Service user: $SERVICE_USER"
echo "• API endpoint: http://$(hostname -I | awk '{print $1}'):8000"
echo "• Documentation: http://$(hostname -I | awk '{print $1}'):8000/"
echo ""
echo -e "${BLUE}🛠️  Service Management Commands:${NC}"
echo "• Start:    sudo systemctl start $SERVICE_NAME"
echo "• Stop:     sudo systemctl stop $SERVICE_NAME"
echo "• Restart:  sudo systemctl restart $SERVICE_NAME"
echo "• Status:   sudo systemctl status $SERVICE_NAME"
echo "• Logs:     sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${BLUE}🔧 Configuration:${NC}"
echo "• Edit config: sudo nano $INSTALL_DIR/.env"
echo "• After config changes: sudo systemctl restart $SERVICE_NAME"
echo ""
echo -e "${YELLOW}🔑 Your API Key: $(grep TURNSTILE_API_KEY $INSTALL_DIR/.env | cut -d'=' -f2)${NC}"
echo ""
echo -e "${BLUE}🧪 Test your API:${NC}"
echo "curl -H \"x-api-key: \$(grep TURNSTILE_API_KEY $INSTALL_DIR/.env | cut -d'=' -f2)\" \\"
echo "     \"http://localhost:8000/turnstile?url=https://example.com&sitekey=test\"" 