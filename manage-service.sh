#!/bin/bash

# Turnstile API Service Management Script
# Usage: ./manage-service.sh [start|stop|restart|status|logs|config|test]

SERVICE_NAME="turnstile-api"
INSTALL_DIR="/opt/turnstile-solver"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if running as root for privileged operations
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}❌ This operation requires root privileges (use sudo)${NC}"
        exit 1
    fi
}

# Function to get API key
get_api_key() {
    if [ -f "$INSTALL_DIR/.env" ]; then
        grep TURNSTILE_API_KEY $INSTALL_DIR/.env | cut -d'=' -f2
    else
        echo "unknown"
    fi
}

# Function to get server IP
get_server_ip() {
    hostname -I | awk '{print $1}'
}

case "$1" in
    start)
        check_root
        echo -e "${YELLOW}🚀 Starting Turnstile API service...${NC}"
        systemctl start $SERVICE_NAME
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✅ Service started successfully${NC}"
        else
            echo -e "${RED}❌ Failed to start service${NC}"
            exit 1
        fi
        ;;
    
    stop)
        check_root
        echo -e "${YELLOW}🛑 Stopping Turnstile API service...${NC}"
        systemctl stop $SERVICE_NAME
        echo -e "${GREEN}✅ Service stopped${NC}"
        ;;
    
    restart)
        check_root
        echo -e "${YELLOW}🔄 Restarting Turnstile API service...${NC}"
        systemctl restart $SERVICE_NAME
        sleep 2
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}✅ Service restarted successfully${NC}"
        else
            echo -e "${RED}❌ Failed to restart service${NC}"
            exit 1
        fi
        ;;
    
    status)
        echo -e "${BLUE}📊 Turnstile API Service Status${NC}"
        echo "================================="
        systemctl status $SERVICE_NAME --no-pager -l
        echo ""
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}🟢 Service is running${NC}"
            echo -e "${BLUE}🌐 API endpoint: http://$(get_server_ip):8000${NC}"
            echo -e "${BLUE}📚 Documentation: http://$(get_server_ip):8000/${NC}"
        else
            echo -e "${RED}🔴 Service is not running${NC}"
        fi
        ;;
    
    logs)
        echo -e "${BLUE}📋 Turnstile API Service Logs${NC}"
        echo "Press Ctrl+C to exit log view"
        echo "================================="
        journalctl -u $SERVICE_NAME -f --no-pager
        ;;
    
    config)
        if [ -f "$INSTALL_DIR/.env" ]; then
            echo -e "${BLUE}⚙️  Current Configuration${NC}"
            echo "================================="
            cat $INSTALL_DIR/.env
            echo ""
            echo -e "${YELLOW}📝 To edit configuration:${NC}"
            echo "sudo nano $INSTALL_DIR/.env"
            echo ""
            echo -e "${YELLOW}⚠️  After editing, restart the service:${NC}"
            echo "sudo ./manage-service.sh restart"
        else
            echo -e "${RED}❌ Configuration file not found at $INSTALL_DIR/.env${NC}"
        fi
        ;;
    
    test)
        if systemctl is-active --quiet $SERVICE_NAME; then
            API_KEY=$(get_api_key)
            SERVER_IP=$(get_server_ip)
            echo -e "${BLUE}🧪 Testing Turnstile API${NC}"
            echo "================================="
            echo -e "${YELLOW}Testing connection...${NC}"
            
            # Test basic connectivity
            if curl -s -f "http://localhost:8000/" > /dev/null; then
                echo -e "${GREEN}✅ API server is responding${NC}"
                
                echo -e "${YELLOW}Testing API endpoint...${NC}"
                response=$(curl -s -H "x-api-key: $API_KEY" \
                    "http://localhost:8000/turnstile?url=https://example.com&sitekey=test" || echo "failed")
                
                if [[ "$response" == *"task_id"* ]]; then
                    echo -e "${GREEN}✅ API endpoint is working${NC}"
                    echo -e "${BLUE}Response: $response${NC}"
                else
                    echo -e "${RED}❌ API endpoint test failed${NC}"
                    echo -e "${RED}Response: $response${NC}"
                fi
            else
                echo -e "${RED}❌ API server is not responding${NC}"
            fi
            
            echo ""
            echo -e "${BLUE}📋 Test Commands:${NC}"
            echo "# Basic connectivity test"
            echo "curl -f http://$SERVER_IP:8000/"
            echo ""
            echo "# API test with your key"
            echo "curl -H \"x-api-key: $API_KEY\" \\"
            echo "     \"http://$SERVER_IP:8000/turnstile?url=https://example.com&sitekey=test\""
        else
            echo -e "${RED}❌ Service is not running. Start it first:${NC}"
            echo "sudo ./manage-service.sh start"
        fi
        ;;
    
    info)
        echo -e "${BLUE}📊 Turnstile API Information${NC}"
        echo "================================="
        echo "Service name: $SERVICE_NAME"
        echo "Install directory: $INSTALL_DIR"
        echo "Configuration file: $INSTALL_DIR/.env"
        echo "Service user: turnstile"
        echo "API Key: $(get_api_key)"
        echo "Server IP: $(get_server_ip)"
        echo ""
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo -e "${GREEN}Status: Running 🟢${NC}"
            echo "API endpoint: http://$(get_server_ip):8000"
            echo "Documentation: http://$(get_server_ip):8000/"
        else
            echo -e "${RED}Status: Stopped 🔴${NC}"
        fi
        ;;
    
    *)
        echo -e "${BLUE}🛠️  Turnstile API Service Manager${NC}"
        echo "================================="
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start the service"
        echo "  stop     - Stop the service"
        echo "  restart  - Restart the service"
        echo "  status   - Show service status"
        echo "  logs     - Show live service logs"
        echo "  config   - Show current configuration"
        echo "  test     - Test API functionality"
        echo "  info     - Show service information"
        echo ""
        echo "Examples:"
        echo "  sudo $0 start"
        echo "  sudo $0 restart"
        echo "  $0 status"
        echo "  $0 logs"
        echo "  $0 test"
        ;;
esac 