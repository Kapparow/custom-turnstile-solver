# 🚀 Public Deployment Guide

This guide covers different methods to deploy your Turnstile API server publicly.

## 🔐 Security First

**⚠️ IMPORTANT**: Always use a strong API key when deploying publicly!

```bash
# Generate a secure API key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📋 Quick Setup Options

### Option 1: Direct Python Deployment

```bash
# 1. Install requirements
pip install -r requirements.txt
pip install hypercorn python-dotenv

# 2. Set environment variables
export TURNSTILE_API_KEY="your-secure-api-key-here"
export HOST="0.0.0.0"
export PORT="8000"
export HEADLESS="true"

# 3. Run production server
python production.py
```

### Option 2: Docker Deployment

```bash
# 1. Copy environment template
cp config.env.template .env

# 2. Edit .env file with your settings
nano .env

# 3. Deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d
```

### Option 3: Command Line (Development)

```bash
python api_solver.py \
  --api-key "your-secure-api-key" \
  --host "0.0.0.0" \
  --port "8000" \
  --headless true \
  --threads 2
```

## 🌐 Reverse Proxy Setup (Recommended)

For production, use nginx as a reverse proxy:

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running captcha solving
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
    }
}
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## ☁️ Cloud Deployment

### DigitalOcean Droplet

```bash
# 1. Create Ubuntu 22.04 droplet (2GB+ RAM recommended)
# 2. SSH into droplet
ssh root@your-server-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Clone your repo
git clone https://github.com/your-username/turnstile-solver.git
cd turnstile-solver

# 5. Configure environment
cp config.env.template .env
nano .env  # Set your API key

# 6. Deploy
docker-compose -f docker-compose.production.yml up -d
```

### AWS EC2

```bash
# Use t3.medium or larger (2GB+ RAM)
# Open ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
# Follow similar steps as DigitalOcean
```

### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/turnstile-api

# Deploy to Cloud Run
gcloud run deploy turnstile-api \
  --image gcr.io/PROJECT-ID/turnstile-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars TURNSTILE_API_KEY="your-key"
```

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TURNSTILE_API_KEY` | API authentication key | *auto-generated* | **Yes** |
| `HOST` | Bind address | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `DEBUG` | Debug mode | `false` | No |
| `HEADLESS` | Browser headless mode | `true` | No |
| `BROWSER_TYPE` | Browser type | `chromium` | No |
| `THREADS` | Browser threads | `2` | No |
| `WORKERS` | Server workers | `1` | No |
| `MAX_CONNECTIONS` | Max connections | `100` | No |

## 🛡️ Security Checklist

- [ ] Strong API key (32+ characters)
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular security updates
- [ ] Rate limiting enabled
- [ ] SSL/TLS certificate installed
- [ ] Non-root user for application
- [ ] Monitor logs for suspicious activity
- [ ] Regular backups

## 📊 Monitoring

### Health Check

```bash
# Check if service is running
curl -f http://your-domain.com/

# Check with API key
curl -H "x-api-key: your-key" \
     "http://your-domain.com/turnstile?url=https://example.com&sitekey=test"
```

### Log Monitoring

```bash
# Docker logs
docker-compose -f docker-compose.production.yml logs -f

# System logs
journalctl -u your-service -f
```

## 🚀 Usage Examples

### Basic Request

```bash
curl -H "x-api-key: your-api-key" \
     "https://your-domain.com/turnstile?url=https://example.com&sitekey=0x4AAAAAAADnPIDROzbs0Akg"
```

### Python Client

```python
import requests

response = requests.get(
    "https://your-domain.com/turnstile",
    headers={"x-api-key": "your-api-key"},
    params={
        "url": "https://example.com",
        "sitekey": "0x4AAAAAAADnPIDROzbs0Akg"
    }
)

task_id = response.json()["task_id"]

# Check result
result = requests.get(
    "https://your-domain.com/result",
    headers={"x-api-key": "your-api-key"},
    params={"id": task_id}
)
```

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 PID
```

**Chrome/Chromium issues:**
```bash
# Add to Docker run command
--shm-size=1g
```

**Memory issues:**
```bash
# Monitor memory usage
docker stats
```

**API key not working:**
```bash
# Check if API key is set correctly
docker-compose -f docker-compose.production.yml exec turnstile-api env | grep API_KEY
```

## 📞 Support

- Check logs for error messages
- Verify firewall and network settings
- Test locally before deploying
- Monitor resource usage (CPU, memory)

---

**🎯 Your API will be accessible at:**
- HTTP: `http://your-domain.com`
- HTTPS: `https://your-domain.com` (with SSL)
- Documentation: `https://your-domain.com/` 