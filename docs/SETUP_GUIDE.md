# Quick Setup Guide for Your Bot

Your bot token has been added to the `.env` file. Here's what you need to do next:

## 1. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click on "API Development Tools"
4. Create a new application (if you haven't already)
5. You'll get:
   - **API ID**: A number like `12345678`
   - **API Hash**: A string like `abcdef1234567890abcdef1234567890`

## 2. Get Your Telegram User ID

1. On Telegram, search for `@userinfobot`
2. Start a chat and send any message
3. The bot will reply with your user ID (a number like `123456789`)

## 3. Get Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the generated key

## 4. Get Vorren API Key (Optional - for Claude models)

If you want to use Claude models (Sonnet):
1. Get a Vorren API key for accessing Claude models
2. This enables access to Anthropic's Claude models via proxy

## 5. Update Your .env File

Edit the `.env` file and replace:
- `your_telegram_api_id` with your API ID
- `your_telegram_api_hash` with your API Hash
- `your_gemini_api_key` with your Gemini API key
- `your_vorren_api_key` with your Vorren API key (optional)
- Update `whitelist.json` with your Telegram user ID

Example `.env`:
```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
GEMINI_API_KEY=AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ
VORREN_API_KEY=your_vorren_key_here  # Optional for Claude models
```

Example `whitelist.json`:
```json
{
  "users": [123456789]
}
```

## 6. Install Dependencies

```bash
pip install -r requirements.txt
```

## 7. Test Your Setup

```bash
# Test basic refactored setup
python test_refactored.py

# Test Anthropic integration (if VORREN_API_KEY is set)
python test_anthropic.py
```

## 8. Run Your Bot

```bash
python main.py
```

## Your Bot Info

Once running, you can find your bot on Telegram by its username and start chatting!

## Available AI Models

Your bot supports multiple AI models:
- **Gemini 2.5 Flash** - Fast responses, good for general use
- **Gemini 2.5 Pro** - More capable, better for complex tasks
- **Claude Sonnet** - Latest Claude model (requires VORREN_API_KEY)
- **O4 Mini** - OpenAI's reasoning model (requires VORREN_API_KEY)
- **GPT-4.1** - OpenAI's non-reasoning model (requires VORREN_API_KEY)
- **GPT-4o** - OpenAI's non-reasoning model (requires VORREN_API_KEY)

Use `/settings` in your bot to switch between models!