#!/bin/bash

# Telethon AI Bot Deployment Script
# This script deploys the bot to a remote server using Ansible

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Telethon AI Bot Deployment${NC}"
echo "================================"

# Check if inventory file exists
if [ ! -f "$SCRIPT_DIR/inventory" ]; then
    echo -e "${RED}Error: inventory file not found!${NC}"
    echo "Please create an inventory file based on inventory.template"
    echo "cp $SCRIPT_DIR/inventory.template $SCRIPT_DIR/inventory"
    echo "Then edit it with your server details"
    exit 1
fi

# Check if ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo -e "${RED}Error: ansible-playbook not found!${NC}"
    echo "Please install Ansible:"
    echo "pip install ansible"
    exit 1
fi

# Parse command line arguments
ACTION="deploy"
if [ "$1" == "restart" ]; then
    ACTION="restart"
elif [ "$1" == "stop" ]; then
    ACTION="stop"
elif [ "$1" == "start" ]; then
    ACTION="start"
elif [ "$1" == "status" ]; then
    ACTION="status"
elif [ "$1" == "logs" ]; then
    ACTION="logs"
fi

case $ACTION in
    deploy)
        echo -e "${YELLOW}Deploying bot to server...${NC}"
        ansible-playbook -i "$SCRIPT_DIR/inventory" "$SCRIPT_DIR/deploy.yml" -v
        echo -e "${GREEN}Deployment complete!${NC}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting bot service...${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m systemd -a "name=telethon-ai-bot state=restarted" --become
        echo -e "${GREEN}Bot restarted!${NC}"
        ;;
    stop)
        echo -e "${YELLOW}Stopping bot service...${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m systemd -a "name=telethon-ai-bot state=stopped" --become
        echo -e "${GREEN}Bot stopped!${NC}"
        ;;
    start)
        echo -e "${YELLOW}Starting bot service...${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m systemd -a "name=telethon-ai-bot state=started" --become
        echo -e "${GREEN}Bot started!${NC}"
        ;;
    status)
        echo -e "${YELLOW}Checking bot status...${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m shell -a "systemctl status telethon-ai-bot" --become
        ;;
    logs)
        echo -e "${YELLOW}Fetching recent logs...${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m shell -a "tail -n 50 /var/log/telethon-ai-bot/bot.log" --become
        echo -e "\n${YELLOW}Recent errors:${NC}"
        ansible telethon_bot -i "$SCRIPT_DIR/inventory" -m shell -a "tail -n 20 /var/log/telethon-ai-bot/error.log" --become
        ;;
    *)
        echo "Usage: $0 [deploy|restart|stop|start|status|logs]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the bot to the server (default)"
        echo "  restart - Restart the bot service"
        echo "  stop    - Stop the bot service"
        echo "  start   - Start the bot service"
        echo "  status  - Check bot service status"
        echo "  logs    - View recent bot logs"
        exit 1
        ;;
esac