#!/bin/bash

# Telethon AI Bot - Systemd Setup Script
# This script sets up the bot as a systemd service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BOT_USER="botuser"
BOT_DIR="/opt/telethon-ai-bot"
SERVICE_FILE="telethon-ai-bot.service"
CURRENT_DIR=$(pwd)

echo -e "${GREEN}Telethon AI Bot - Systemd Setup${NC}"
echo "=================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}" 
   exit 1
fi

# Create bot user if it doesn't exist
if ! id "$BOT_USER" &>/dev/null; then
    echo -e "${YELLOW}Creating user $BOT_USER...${NC}"
    useradd -r -s /bin/bash -m -d /home/$BOT_USER $BOT_USER
    echo -e "${GREEN}User created${NC}"
else
    echo -e "${GREEN}User $BOT_USER already exists${NC}"
fi

# Create bot directory
echo -e "${YELLOW}Creating bot directory...${NC}"
mkdir -p $BOT_DIR
mkdir -p $BOT_DIR/data
mkdir -p $BOT_DIR/logs

# Copy bot files
echo -e "${YELLOW}Copying bot files...${NC}"
cp -r $CURRENT_DIR/* $BOT_DIR/
cp $CURRENT_DIR/.env.example $BOT_DIR/.env.example 2>/dev/null || true
cp $CURRENT_DIR/.env $BOT_DIR/.env 2>/dev/null || true

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
cd $BOT_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Update the service file to use virtual environment
sed -i "s|ExecStart=/usr/bin/python3|ExecStart=$BOT_DIR/venv/bin/python|g" $BOT_DIR/$SERVICE_FILE

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R $BOT_USER:$BOT_USER $BOT_DIR
chmod 750 $BOT_DIR
chmod 640 $BOT_DIR/.env 2>/dev/null || true

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
cp $BOT_DIR/$SERVICE_FILE /etc/systemd/system/
systemctl daemon-reload

# Create .env file if it doesn't exist
if [ ! -f "$BOT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp $BOT_DIR/.env.example $BOT_DIR/.env
    echo -e "${RED}Please edit $BOT_DIR/.env with your API credentials${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit the .env file: sudo nano $BOT_DIR/.env"
echo "2. Enable the service: sudo systemctl enable telethon-ai-bot"
echo "3. Start the service: sudo systemctl start telethon-ai-bot"
echo "4. Check status: sudo systemctl status telethon-ai-bot"
echo "5. View logs: sudo journalctl -u telethon-ai-bot -f"
echo ""
echo "To uninstall:"
echo "sudo systemctl stop telethon-ai-bot"
echo "sudo systemctl disable telethon-ai-bot"
echo "sudo rm /etc/systemd/system/telethon-ai-bot.service"
echo "sudo rm -rf $BOT_DIR"
echo "sudo userdel -r $BOT_USER"