# Telethon AI Bot - Refactored Architecture

A modular Telegram bot with AI capabilities, featuring a clean architecture that makes it easy to extend and maintain.

## 🏗️ Project Structure

```
telethon-ai-bot/
├── src/
│   ├── bot/                    # Bot-specific modules
│   │   ├── __init__.py
│   │   ├── commands.py         # Command handlers (/start, /help, etc.)
│   │   ├── callbacks.py        # Callback query handlers (inline buttons)
│   │   ├── handlers.py         # Message handlers (AI responses)
│   │   └── decorators.py       # Authorization decorator
│   │
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py         # Settings from environment
│   │   └── whitelist.py        # Whitelist manager with caching
│   │
│   ├── database/               # Database layer
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   └── manager.py          # Database operations
│   │
│   ├── llm/                    # LLM integrations
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base class for LLMs
│   │   ├── gemini.py           # Google Gemini implementation
│   │   ├── anthropic.py        # Anthropic Claude implementation
│   │   ├── openai.py           # OpenAI GPT implementation
│   │   └── factory.py          # Factory for creating LLM clients
│   │
│   ├── utils/                  # Utility modules
│   │   ├── __init__.py
│   │   └── message_utils.py    # Message splitting utilities
│   │
│   └── main.py                 # Application entry point
│
├── tests/                      # Test directory (ready for tests)
├── docs/                       # Documentation directory
├── main.py                     # Root entry point
├── whitelist.json              # User whitelist
├── .env                        # Environment configuration
└── requirements.txt            # Python dependencies
```

## 🚀 Key Features

### Modular Architecture
- **Clean separation of concerns**: Each module has a specific responsibility
- **Easy to extend**: Add new LLM providers, commands, or features
- **Testable**: Each component can be tested independently

### Configuration Management
- **Environment-based**: All settings in `.env` file
- **Type-safe**: Settings class with validation
- **Cached whitelist**: 60-second cache for performance

### Database Layer
- **Async SQLAlchemy**: Non-blocking database operations
- **Clean models**: User, Conversation, and Message entities
- **Manager pattern**: All DB operations through DatabaseManager

### LLM Integration
- **Multiple providers**: Gemini, Claude, and OpenAI models supported
- **Provider agnostic**: Easy to add new AI providers
- **Factory pattern**: Switch between providers easily
- **Thinking mode**: Support for advanced reasoning
- **Available models**:
  - Gemini 2.5 Flash & Pro
  - Claude Sonnet 4, Claude 3.7 Sonnet, Claude 3.5 Sonnet
  - O4 Mini (Reasoning), GPT-4.1, GPT-4o

### Bot Features
- **Command handlers**: Modular command system
- **Callback handlers**: Interactive inline buttons
- **Message handlers**: AI conversation handling
- **Authorization**: Decorator-based access control

## 🔧 Adding New Features

### Adding a New LLM Provider

1. Create a new file in `src/llm/`:
```python
# src/llm/openai.py
from .base import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    async def generate_response(self, messages, model_name, max_tokens, temperature, thinking_mode=False):
        # Implementation here
        pass
    
    def get_available_models(self):
        return {"gpt-4": "gpt-4", "gpt-3.5": "gpt-3.5-turbo"}
    
    def supports_thinking_mode(self):
        return False
```

2. Register in the factory:
```python
# src/llm/factory.py
from .openai import OpenAIClient

LLMFactory.register_provider("openai", OpenAIClient)
```

### Adding a New Command

1. Add to `src/bot/commands.py`:
```python
@require_authorization
async def handle_stats(self, event):
    """Handle /stats command"""
    # Implementation here
    pass
```

2. Register the handler:
```python
def register_handlers(self):
    # ... existing handlers ...
    self.client.add_event_handler(
        self.handle_stats,
        events.NewMessage(pattern='/stats')
    )
```

### Adding Database Models

1. Add to `src/database/models.py`:
```python
class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. Add methods to `src/database/manager.py`:
```python
async def log_analytics(self, user_id: int, event_type: str):
    """Log an analytics event"""
    # Implementation here
```

## 🔐 Security

- **Whitelist-based access**: Only authorized users in `whitelist.json`
- **60-second cache**: Balance between security and performance
- **No bot commands can modify whitelist**: Manual edit only
- **Environment variables**: Sensitive data in `.env`

## 🚦 Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the bot
python main.py
```

## 📝 Configuration

### Environment Variables (.env)
```env
# Telegram
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# Gemini API
GEMINI_API_KEY=your_gemini_key

# Database
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
```

### Whitelist (whitelist.json)
```json
{
  "authorized_users": [
    123456789,
    987654321
  ],
  "comments": {
    "123456789": "Admin user",
    "987654321": "Friend"
  }
}
```

## 🧪 Testing

The modular structure makes testing easy:

```python
# tests/test_whitelist.py
from src.config import WhitelistManager

def test_whitelist_caching():
    manager = WhitelistManager(cache_ttl=1)
    users = manager.get_authorized_users()
    # Test implementation
```

## 🔄 Migration from Old Structure

The refactored code maintains full compatibility with the existing database and configuration. Simply:

1. Move your `.env` file to the root
2. Move your `whitelist.json` to the root
3. Your existing database will work as-is
4. Run `python main.py` instead of the old main.py

## 📚 Benefits of the New Structure

1. **Maintainability**: Clear module boundaries make code easier to understand
2. **Extensibility**: Add new features without touching existing code
3. **Testability**: Each component can be tested in isolation
4. **Scalability**: Easy to add new LLM providers, commands, or features
5. **Type Safety**: Better IDE support and fewer runtime errors
6. **Performance**: Efficient caching and async operations throughout

This refactored architecture provides a solid foundation for future enhancements while maintaining all existing functionality.