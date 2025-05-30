#!/bin/bash

# Run Telethon AI Bot with Doppler secrets

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Telethon AI Bot - Flexible Environment${NC}"
echo "========================================"

# Check if DOPPLER_TOKEN is set
if [ -n "$DOPPLER_TOKEN" ]; then
    # Check if ENVIRONMENT is set
    if [ -n "$ENVIRONMENT" ]; then
        # Validate ENVIRONMENT
        if [ "$ENVIRONMENT" != "DEV" ] && [ "$ENVIRONMENT" != "PROD" ]; then
            echo -e "${YELLOW}Warning: ENVIRONMENT must be either DEV or PROD${NC}"
            echo -e "${YELLOW}Falling back to .env file${NC}"
        else
            echo -e "${GREEN}Using Doppler secrets (Environment: $ENVIRONMENT)${NC}"
        fi
    else
        echo -e "${YELLOW}ENVIRONMENT not set, falling back to .env file${NC}"
    fi
else
    echo -e "${YELLOW}DOPPLER_TOKEN not set, using .env file${NC}"
fi

echo -e "${GREEN}Starting bot...${NC}"
echo ""

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we're in a virtual environment setup (deployment)
if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    echo -e "${BLUE}Using virtual environment${NC}"
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python"
else
    # Use system python
    PYTHON_CMD="python3"
fi

# Run the bot
$PYTHON_CMD "$SCRIPT_DIR/main.py"

# Exit with the same code as the Python script
exit $?