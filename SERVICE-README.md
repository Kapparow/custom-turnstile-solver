# 🚀 Turnstile API System Service for Ubuntu

This guide shows how to run your Turnstile API as a proper Linux system service that starts automatically on boot and restarts on failures.

## 📦 Quick Installation

### One-Command Installation

```bash
sudo bash install-service.sh
```

This automatically:
- ✅ Creates system user (`turnstile`)
- ✅ Installs dependencies (Chrome, Python packages)
- ✅ Sets up virtual environment
- ✅ Generates secure API key
- ✅ Creates systemd service
- ✅ Configures firewall
- ✅ Starts the service

## 🛠️ Service Management

### Using the Management Script

```bash
# Start the service
sudo ./manage-service.sh start

# Stop the service  
sudo ./manage-service.sh stop

# Restart the service
sudo ./manage-service.sh restart

# Check service status
./manage-service.sh status

# View live logs
./manage-service.sh logs

# Show configuration
./manage-service.sh config

# Test API functionality
./manage-service.sh test

# Show service info
./manage-service.sh info
```

### Using Standard systemctl Commands

```bash
# Service control
sudo systemctl start turnstile-api
sudo systemctl stop turnstile-api
sudo systemctl restart turnstile-api
sudo systemctl status turnstile-api

# Enable/disable auto-start
sudo systemctl enable turnstile-api
sudo systemctl disable turnstile-api

# View logs
sudo journalctl -u turnstile-api -f
sudo journalctl -u turnstile-api --since today
sudo journalctl -u turnstile-api --lines 100
```

## ⚙️ Configuration

### Environment File
Configuration is stored in `/opt/turnstile-solver/.env`:

```bash
# Edit configuration
sudo nano /opt/turnstile-solver/.env

# Restart service after changes
sudo systemctl restart turnstile-api
```

### Default Configuration
```env
TURNSTILE_API_KEY=your-secure-api-key-here
HOST=0.0.0.0
PORT=8000
DEBUG=false
HEADLESS=true
BROWSER_TYPE=chromium
THREADS=2
WORKERS=1
MAX_CONNECTIONS=100
```

## 📊 Service Details

| Setting | Value |
|---------|-------|
| **Service Name** | `turnstile-api` |
| **User** | `turnstile` |
| **Install Directory** | `/opt/turnstile-solver` |
| **Configuration** | `/opt/turnstile-solver/.env` |
| **Logs** | `journalctl -u turnstile-api` |
| **Port** | `8000` |
| **Auto-start** | Yes (enabled by default) |
| **Auto-restart** | Yes (on failure) |

## 🔒 Security Features

- ✅ **Non-root user**: Runs as `turnstile` system user
- ✅ **Isolated directory**: Protected `/opt/turnstile-solver`
- ✅ **Secure permissions**: API key file (600 permissions)
- ✅ **System hardening**: NoNewPrivileges, ProtectSystem
- ✅ **Resource limits**: Memory and file descriptor limits
- ✅ **Firewall rules**: UFW configured for port 8000

## 🧪 Testing

### Quick Test
```bash
# Test with management script
./manage-service.sh test

# Manual test
API_KEY=$(sudo grep TURNSTILE_API_KEY /opt/turnstile-solver/.env | cut -d'=' -f2)
curl -H "x-api-key: $API_KEY" \
     "http://localhost:8000/turnstile?url=https://example.com&sitekey=test"
```

### Health Check
```bash
# Basic connectivity
curl -f http://localhost:8000/

# Service status
systemctl is-active turnstile-api && echo "Running" || echo "Stopped"
```

## 📋 Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status turnstile-api

# Check logs
sudo journalctl -u turnstile-api -n 50

# Check configuration
sudo ./manage-service.sh config
```

### Common Issues

**Permission denied errors:**
```bash
# Fix ownership
sudo chown -R turnstile:turnstile /opt/turnstile-solver
```

**Port already in use:**
```bash
# Check what's using port 8000
sudo lsof -i :8000
sudo netstat -tulpn | grep :8000
```

**Chrome/browser issues:**
```bash
# Check Chrome installation
google-chrome --version

# Test headless mode
sudo -u turnstile google-chrome --headless --no-sandbox --version
```

**API key issues:**
```bash
# Check API key
sudo grep TURNSTILE_API_KEY /opt/turnstile-solver/.env

# Generate new API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Log Analysis

```bash
# Error logs only
sudo journalctl -u turnstile-api -p err

# Logs from last hour
sudo journalctl -u turnstile-api --since "1 hour ago"

# Follow logs in real-time
sudo journalctl -u turnstile-api -f
```

## 🔄 Updates

### Update Application Code
```bash
# Stop service
sudo systemctl stop turnstile-api

# Update code
cd /opt/turnstile-solver
sudo -u turnstile git pull

# Install any new dependencies
sudo -u turnstile /opt/turnstile-solver/venv/bin/pip install -r requirements.txt

# Start service
sudo systemctl start turnstile-api
```

### Change Configuration
```bash
# Edit settings
sudo nano /opt/turnstile-solver/.env

# Restart to apply changes
sudo systemctl restart turnstile-api
```

## 🌐 External Access

The service runs on `0.0.0.0:8000` by default, making it accessible from:

- **Local**: `http://localhost:8000`
- **Network**: `http://YOUR-SERVER-IP:8000`
- **Documentation**: `http://YOUR-SERVER-IP:8000/`

### Firewall Configuration
```bash
# Allow port 8000
sudo ufw allow 8000/tcp

# Check firewall status
sudo ufw status
```

## 🚨 Uninstall

```bash
# Stop and disable service
sudo systemctl stop turnstile-api
sudo systemctl disable turnstile-api

# Remove service file
sudo rm /etc/systemd/system/turnstile-api.service
sudo systemctl daemon-reload

# Remove user and directory
sudo userdel -r turnstile
sudo rm -rf /opt/turnstile-solver

# Remove firewall rule
sudo ufw delete allow 8000/tcp
```

---

## 📞 Support

For issues or questions:
1. Check service logs: `sudo journalctl -u turnstile-api`
2. Verify configuration: `./manage-service.sh config`
3. Test functionality: `./manage-service.sh test`
4. Check service status: `./manage-service.sh status` 