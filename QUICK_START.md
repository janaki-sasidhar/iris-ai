# Telethon AI Bot - Quick Start

## 🚀 Fastest Setup

### Option 1: Docker (Recommended)
```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 2. Start with Docker
cd docker
./docker-start.sh
```

### Option 2: Direct Python
```bash
# 1. Setup
python scripts/setup.py

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

### Option 3: Systemd Service
```bash
sudo scripts/setup-systemd.sh
```

## 📁 Project Structure

- **`src/`** - Source code (bot, config, database, LLM clients)
- **`docker/`** - Docker deployment files
- **`scripts/`** - Setup and deployment scripts
- **`docs/`** - Detailed documentation

## 📚 Documentation

- [Full README](README.md) - Complete project documentation
- [Deployment Guide](docs/DEPLOYMENT.md) - Detailed deployment instructions
- [Setup Guide](docs/SETUP_GUIDE.md) - Configuration help

## 🔑 Required Credentials

1. **Telegram**: API ID, API Hash, Bot Token
2. **OpenAI**: OPENAI_API_KEY
3. **Google Cloud (Vertex AI)**: Authenticate with gcloud (ADC)

Quick steps:
- Telegram: https://my.telegram.org & @BotFather
- OpenAI: https://platform.openai.com/
- Vertex AI: `gcloud auth application-default login` and `gcloud config set project play-hoa`
