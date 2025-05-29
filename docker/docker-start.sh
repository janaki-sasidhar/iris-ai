#!/bin/bash

# Telethon AI Bot - Docker Quick Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Telethon AI Bot - Docker Setup     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists in parent directory
if [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp ../.env.example ../.env
    echo -e "${RED}Please edit .env file with your API credentials before continuing${NC}"
    echo -e "${YELLOW}Run: nano ../.env${NC}"
    exit 1
fi

# Create necessary directories in parent
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p ../data ../logs

# Check if whitelist.json exists
if [ ! -f "../whitelist.json" ]; then
    echo -e "${YELLOW}Creating empty whitelist.json...${NC}"
    echo '{"authorized_users": []}' > ../whitelist.json
fi

# Change to docker directory if not already there
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker-compose build

# Start the bot
echo -e "${YELLOW}Starting Telethon AI Bot...${NC}"
docker-compose up -d

# Wait a moment for container to start
sleep 3

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Bot started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Useful commands (run from docker/ directory):${NC}"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop bot:         docker-compose down"
    echo "  Restart bot:      docker-compose restart"
    echo "  View status:      docker-compose ps"
    echo ""
    echo -e "${YELLOW}Viewing initial logs (press Ctrl+C to exit)...${NC}"
    docker-compose logs -f
else
    echo -e "${RED}✗ Failed to start bot${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi