# Telethon AI Bot - Quick Start Guide

## 🚀 Quick Start with Docker (Recommended)

### 1. Prerequisites
- Docker and Docker Compose installed
- Telegram API credentials (get from https://my.telegram.org)
- Bot token (get from @BotFather on Telegram)
- Google Cloud gcloud CLI configured (ADC) for Vertex AI

### 2. Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd telethon-ai-bot

# Create environment file
cp .env.example .env

# Install uv and sync deps (if not using Docker for local dev)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv && source .venv/bin/activate
uv sync

# Edit .env with your credentials (OpenAI + optional GCP overrides)
nano .env  # or use your preferred editor
```

### 3. Run with Docker
```bash
# Quick start (automated)
./docker-start.sh

# Or manually:
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔧 Alternative: Systemd Service

### For production servers without Docker:
```bash
# Run the automated setup
sudo ./setup-systemd.sh

# Edit configuration
sudo nano /opt/telethon-ai-bot/.env

# Start the service
sudo systemctl start telethon-ai-bot
sudo systemctl enable telethon-ai-bot
```

## 📁 Files Created

### Docker Deployment
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Service orchestration
- `docker-start.sh` - Quick start script
- `.dockerignore` - Build optimization

### Systemd Deployment
- `telethon-ai-bot.service` - Service definition
- `setup-systemd.sh` - Automated setup script

### Documentation
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOYMENT_QUICKSTART.md` - This file

## 🛠️ Common Commands

### Docker
```bash
# Start bot
docker-compose up -d

# Stop bot
docker-compose down

# View logs
docker-compose logs -f

# Restart bot
docker-compose restart

# Update bot
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Systemd
```bash
# Start bot
sudo systemctl start telethon-ai-bot

# Stop bot
sudo systemctl stop telethon-ai-bot

# View logs
sudo journalctl -u telethon-ai-bot -f

# Restart bot
sudo systemctl restart telethon-ai-bot

# Check status
sudo systemctl status telethon-ai-bot
```

## 📝 Configuration

Edit `.env` file (OpenAI + optional GCP overrides):
```env
# Required
API_ID=12345678
API_HASH=your_api_hash_here
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
OPENAI_API_KEY=your_openai_key_here
GCP_PROJECT=play-hoa
GCP_LOCATION=global

# Optional
VORREN_API_KEY=your_vorren_key_here
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
```

## 🔍 Troubleshooting

1. **Bot not responding?**
   - Check logs for errors
   - Verify API credentials
   - Ensure bot is added to chat/group

2. **Permission errors?**
   - Docker: Check file ownership
   - Systemd: Run setup script as root

3. **Can't connect to Telegram?**
   - Check network connectivity
   - Verify API_ID and API_HASH
   - Delete session file and restart

## 📚 More Information

See `DEPLOYMENT.md` for detailed instructions, troubleshooting, and advanced configuration options.
