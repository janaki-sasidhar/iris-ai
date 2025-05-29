# Telethon AI Bot - Deployment Guide

This guide provides instructions for deploying the Telethon AI Bot using Docker or systemd.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for Docker deployment)
- systemd-based Linux system (for systemd deployment)
- Telegram API credentials (API ID, API Hash, Bot Token)
- Gemini API key
- Optional: Vorren API key for Claude models

## Configuration

Before deployment, create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
# Telegram API Configuration
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Vorren API Configuration (for Claude models)
VORREN_API_KEY=your_vorren_api_key_here

# Database Configuration (optional, defaults to SQLite)
# DATABASE_URL=sqlite+aiosqlite:///bot_database.db
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the bot in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### 2. Docker Commands

```bash
# Build the image manually
docker build -t telethon-ai-bot .

# Run the container manually
docker run -d \
  --name telethon-ai-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/whitelist.json:/app/whitelist.json \
  --restart unless-stopped \
  telethon-ai-bot

# View container logs
docker logs -f telethon-ai-bot

# Stop and remove container
docker stop telethon-ai-bot
docker rm telethon-ai-bot
```

### 3. Docker Compose Features

- Automatic restart on failure
- Volume mounts for persistent data
- Log rotation (10MB max, 3 files)
- Isolated network
- Environment file support

## Systemd Deployment

### 1. Automated Setup

Run the setup script as root:

```bash
sudo chmod +x setup-systemd.sh
sudo ./setup-systemd.sh
```

### 2. Manual Setup

If you prefer manual setup:

```bash
# Create bot user
sudo useradd -r -s /bin/bash -m -d /home/botuser botuser

# Create bot directory
sudo mkdir -p /opt/telethon-ai-bot
sudo mkdir -p /opt/telethon-ai-bot/data
sudo mkdir -p /opt/telethon-ai-bot/logs

# Copy files
sudo cp -r * /opt/telethon-ai-bot/
sudo cp .env /opt/telethon-ai-bot/

# Create virtual environment
cd /opt/telethon-ai-bot
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# Set permissions
sudo chown -R botuser:botuser /opt/telethon-ai-bot
sudo chmod 750 /opt/telethon-ai-bot
sudo chmod 640 /opt/telethon-ai-bot/.env

# Install service
sudo cp telethon-ai-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 3. Service Management

```bash
# Enable auto-start on boot
sudo systemctl enable telethon-ai-bot

# Start the service
sudo systemctl start telethon-ai-bot

# Check status
sudo systemctl status telethon-ai-bot

# View logs
sudo journalctl -u telethon-ai-bot -f

# Restart service
sudo systemctl restart telethon-ai-bot

# Stop service
sudo systemctl stop telethon-ai-bot

# Disable auto-start
sudo systemctl disable telethon-ai-bot
```

### 4. Systemd Service Features

- Automatic restart on failure (max 3 attempts in 60 seconds)
- Resource limits (512MB memory, 50% CPU)
- Security hardening (read-only system, private tmp)
- Journal logging
- Environment file support

## Directory Structure

```
/opt/telethon-ai-bot/           # Main bot directory (systemd)
├── data/                       # Persistent data
├── logs/                       # Log files
├── venv/                       # Python virtual environment
├── src/                        # Source code
├── .env                        # Environment variables
├── whitelist.json              # Authorized users
├── bot_database.db            # SQLite database
└── bot_session.session        # Telegram session
```

## Maintenance

### Updating the Bot

#### Docker:
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

#### Systemd:
```bash
# Stop the service
sudo systemctl stop telethon-ai-bot

# Update files
cd /opt/telethon-ai-bot
sudo -u botuser git pull

# Update dependencies
sudo -u botuser ./venv/bin/pip install -r requirements.txt

# Restart service
sudo systemctl start telethon-ai-bot
```

### Backup

Important files to backup:
- `.env` - Configuration
- `whitelist.json` - Authorized users
- `bot_database.db` - Conversation history
- `bot_session.session` - Telegram session
- `data/` directory - Any additional data

### Monitoring

#### Docker:
```bash
# Check container status
docker ps

# Monitor resource usage
docker stats telethon-ai-bot

# Check logs for errors
docker-compose logs --tail=100 | grep ERROR
```

#### Systemd:
```bash
# Check service status
sudo systemctl status telethon-ai-bot

# Monitor logs
sudo journalctl -u telethon-ai-bot -f

# Check for errors
sudo journalctl -u telethon-ai-bot --since "1 hour ago" | grep ERROR
```

## Troubleshooting

### Common Issues

1. **Bot not responding:**
   - Check logs for errors
   - Verify API credentials in `.env`
   - Ensure bot token is valid
   - Check network connectivity

2. **Database errors:**
   - Check file permissions
   - Ensure write access to data directory
   - Verify DATABASE_URL in `.env`

3. **Memory issues:**
   - Increase memory limit in systemd service or docker-compose
   - Check for memory leaks in logs
   - Monitor resource usage

4. **Permission denied:**
   - Check file ownership (should be botuser:botuser)
   - Verify directory permissions
   - Ensure SELinux is not blocking (if applicable)

### Debug Mode

To run in debug mode:

```bash
# Docker
docker-compose run --rm telethon-bot python main.py

# Systemd (as botuser)
sudo -u botuser /opt/telethon-ai-bot/venv/bin/python /opt/telethon-ai-bot/main.py
```

## Security Recommendations

1. **Use strong API keys** - Generate secure API keys and tokens
2. **Restrict file permissions** - Keep `.env` readable only by bot user
3. **Regular updates** - Keep dependencies updated
4. **Monitor logs** - Check for suspicious activity
5. **Backup regularly** - Automate backups of important data
6. **Use firewall** - Restrict outbound connections if needed
7. **Rotate credentials** - Periodically update API keys

## Uninstallation

### Docker:
```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi telethon-ai-bot

# Remove volumes (careful - this deletes data!)
docker volume prune
```

### Systemd:
```bash
# Stop and disable service
sudo systemctl stop telethon-ai-bot
sudo systemctl disable telethon-ai-bot

# Remove service file
sudo rm /etc/systemd/system/telethon-ai-bot.service
sudo systemctl daemon-reload

# Remove bot directory
sudo rm -rf /opt/telethon-ai-bot

# Remove bot user
sudo userdel -r botuser
```

## Support

For issues or questions:
1. Check the logs first
2. Review the troubleshooting section
3. Ensure all dependencies are installed
4. Verify configuration in `.env`
5. Check file permissions