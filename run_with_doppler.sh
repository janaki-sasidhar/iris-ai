#!/bin/bash

# Run Telethon AI Bot with Doppler secrets

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Telethon AI Bot - Doppler Integration${NC}"
echo "========================================"

# Check if DOPPLER_TOKEN is set
if [ -z "$DOPPLER_TOKEN" ]; then
    echo -e "${RED}Error: DOPPLER_TOKEN environment variable is not set${NC}"
    echo "Please set it with: export DOPPLER_TOKEN=dp.pt.your-token-here"
    exit 1
fi

# Check if ENVIRONMENT is set
if [ -z "$ENVIRONMENT" ]; then
    echo -e "${RED}Error: ENVIRONMENT environment variable is not set${NC}"
    echo "Please set it with: export ENVIRONMENT=DEV (or PROD)"
    exit 1
fi

# Validate ENVIRONMENT
if [ "$ENVIRONMENT" != "DEV" ] && [ "$ENVIRONMENT" != "PROD" ]; then
    echo -e "${RED}Error: ENVIRONMENT must be either DEV or PROD${NC}"
    exit 1
fi

echo -e "${GREEN}Starting bot with Doppler secrets (Environment: $ENVIRONMENT)...${NC}"
echo ""

# Run the bot
python main.py

# Exit with the same code as the Python script
exit $?