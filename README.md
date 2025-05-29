# Telethon AI Bot

A Telegram bot built with Telethon (async) that integrates with multiple AI providers (Gemini, Claude, OpenAI) to provide conversational AI capabilities with context persistence.

## Features

- **Access Control**: Whitelist-based authorization system
- **Conversation Management**:
  - Persistent conversation context across messages
  - `/newchat` command to start fresh conversations
- **Multi-modal Support**: Handle both text and image inputs
- **Multiple AI Providers**:
  - Google Gemini (Flash & Pro)
  - Anthropic Claude (Sonnet models)
  - OpenAI (GPT-4, O4 reasoning models)
- **Advanced Features**:
  - Thinking mode for detailed reasoning
  - Gemini Search for web-based information (Gemini models only)
  - Adjustable temperature and response settings
- **Database Persistence**: SQLite database for storing conversations and user settings

## Prerequisites

- Python 3.8 or higher
- Telegram API credentials (API ID and API Hash)
- Telegram Bot Token
- Google Gemini API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telethon-ai-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Configure your `.env` file:
```env
# Telegram Bot Configuration
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_bot_token

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# Optional: Vorren API Configuration (for Claude models)
VORREN_API_KEY=your_vorren_api_key

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
```

5. Configure authorized users in `whitelist.json`:
```json
{
  "authorized_users": [123456789, 987654321]
}
```

### Quick Setup

For a guided setup process, run:
```bash
python scripts/setup.py
```

This will help you:
- Install dependencies
- Rename `.env.example` to `.env` and configure your credentials
- Verify your Python version

### Getting Telegram Credentials

1. **API ID and API Hash**:
   - Go to https://my.telegram.org
   - Log in with your phone number
   - Go to "API Development Tools"
   - Create a new application
   - Copy the API ID and API Hash

2. **Bot Token**:
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow the instructions
   - Copy the bot token provided

3. **User IDs for Whitelist**:
   - You can get user IDs by using @userinfobot on Telegram
   - Send any message to the bot to get your user ID
   - Add the user IDs to `whitelist.json` file (not .env)

### Getting Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy and add it to your `.env` file

## Testing

Before running the bot, you can verify your configuration:
```bash
python scripts/setup.py
```

This will help you:
- Create the .env file
- Configure API credentials
- Set up the whitelist

## Deployment

### Quick Start with Docker
```bash
cd docker
./docker-start.sh
```

### Manual Docker Commands
```bash
cd docker
docker-compose up -d
docker-compose logs -f
```

### Systemd Service
```bash
sudo scripts/setup-systemd.sh
```

For detailed deployment instructions, see:
- `docs/DEPLOYMENT_QUICKSTART.md` - Quick start guide
- `docs/DEPLOYMENT.md` - Comprehensive deployment guide

## Usage

1. Start the bot:
```bash
python main.py
```

2. In Telegram, start a conversation with your bot

3. Available commands:
   - `/start` - Initialize the bot and see welcome message
   - `/newchat` - Start a new conversation (clears context)
   - `/settings` - Configure model, max tokens, and temperature
   - `!ping` - Bot responds with `!pong` (simple connectivity test)

4. Send messages:
   - Text messages for questions
   - Images with captions for visual queries
   - The bot maintains conversation context until `/newchat` is used

## Project Structure

```
telethon-ai-bot/
├── main.py              # Bot entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── whitelist.json       # Authorized users list
├── README.md            # This file
├── src/                 # Source code
│   ├── bot/            # Bot handlers and decorators
│   ├── config/         # Configuration and settings
│   ├── database/       # Database models and manager
│   ├── llm/            # LLM clients (Gemini, Claude, OpenAI)
│   └── utils/          # Utility functions
├── docker/             # Docker deployment files
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-start.sh
├── scripts/            # Setup and deployment scripts
│   ├── setup.py        # Interactive setup script
│   ├── setup-systemd.sh
│   └── telethon-ai-bot.service
└── docs/               # Documentation
    ├── DEPLOYMENT.md
    ├── DEPLOYMENT_QUICKSTART.md
    └── SETUP_GUIDE.md
```

## Database Schema

The bot uses SQLite with three main tables:
- **users**: Stores user information and settings
- **conversations**: Manages conversation sessions
- **messages**: Stores message history for context

## Security Notes

- Only whitelisted user IDs can interact with the bot
- Non-authorized users receive "Not authorized." message
- API keys and tokens should never be committed to version control
- The `.gitignore` file excludes sensitive files

## Extending the Bot

The modular design allows easy extensions:
- Add new commands in `handlers.py`
- Integrate additional AI models in `gemini_client.py`
- Extend database schema in `database.py`
- Add new configuration options in `config.py`

## Troubleshooting

1. **"Not authorized" message**: Ensure your Telegram user ID is in the WHITELISTED_USERS
2. **Database errors**: Delete `bot_database.db` to recreate the database
3. **API errors**: Verify your API keys are correct and have proper permissions
4. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

## License

This project is provided as-is for educational and personal use.

## 📋 TODO / Future Enhancements

- [ ] **Database Support**: Add PostgreSQL support alongside SQLite for production deployments
- [ ] **Additional LLM Providers**:
  - [ ] Groq AI integration
  - [ ] DeepSeek integration
- [ ] **Enhanced Access Control**:
  - [ ] Super admin role with ability to manage whitelist
  - [ ] Role-based permissions (admin, user, viewer)
- [ ] **Persistent Remote Database**:
  - [ ] Store whitelist in database instead of JSON file
  - [ ] User management API/interface
  - [ ] Audit logs for admin actions
- [ ] **Maintenance Scripts**:
  - [ ] Automated conversation cleanup (cron jobs)
  - [ ] Database backup scripts
  - [ ] Log rotation and cleanup
  - [ ] Usage statistics and reporting
- [x] **Additional Features**:
  - [x] Gemini Search for web-based information
  - [ ] Web dashboard for bot management
  - [ ] Webhook support for better performance
  - [ ] Multi-language support
  - [ ] Rate limiting per user
  - [ ] Export conversation history