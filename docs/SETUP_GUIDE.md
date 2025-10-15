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

## 3. Authenticate Google Cloud (Vertex AI)

Use ADC via gcloud so the bot can call Vertex AI for Gemini and Claude:
```bash
gcloud auth application-default login
gcloud config set project play-hoa
```
Set optional `.env` vars:
```env
GCP_PROJECT=play-hoa
GCP_LOCATION=global
```

## 4. Get OpenAI API Key

Add your OpenAI API key to `.env` as `OPENAI_API_KEY`.

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
OPENAI_API_KEY=sk-...
GCP_PROJECT=play-hoa
GCP_LOCATION=global
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

- Gemini 2.5 Flash / Pro (Vertex)
- Claude Sonnet 4.5 / Opus 4.1 (Vertex)
- GPT‑5 / GPT‑5 Chat (OpenAI)

Use `/settings` to switch and configure provider-specific options.
