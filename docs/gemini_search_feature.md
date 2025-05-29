# Gemini Search Feature

## Overview

The bot now supports web search functionality exclusively for Google Gemini models. When enabled, Gemini can search the web to provide more accurate and up-to-date information in its responses.

## How It Works

1. **Enable Gemini Search**: Toggle Gemini Search on/off in the settings menu (`/settings`)
2. **Automatic Search**: Gemini will automatically search the web when needed based on your query
3. **Integrated Results**: Search results are seamlessly integrated into the response

## Usage

### Enabling Gemini Search

1. Send `/settings` to the bot
2. Select a Gemini model (Flash or Pro)
3. Select "🔍 Gemini Search" 
4. Toggle between ON/OFF

### Example Queries That May Trigger Search

- "What's the latest news about [topic]?"
- "What are the current prices of [product]?"
- "What happened in [recent event]?"
- "What's the weather in [location]?"
- "What are the latest updates to [technology]?"

### Response Format

When Gemini Search is used, you'll see:

```
🔍 *Web search used*

Your answer with integrated search results.
```

The response seamlessly integrates web search results without showing additional metadata.

## Technical Implementation

### Google Search Tool

The feature uses Google's native search integration:

```python
from google.genai.types import Tool, GoogleSearch

google_search_tool = Tool(
    google_search=GoogleSearch()
)
```

### Configuration

When Gemini Search is enabled, the bot adds the search tool to the generation config:

```python
config = GenerateContentConfig(
    tools=[google_search_tool],
    response_modalities=["TEXT"],
    temperature=temperature
)
```

## Supported Models

Gemini Search is available for all Gemini models:
- Gemini 2.5 Flash
- Gemini 2.5 Pro

## Privacy & Security

- Search queries are processed by Google's servers
- No search history is stored locally by the bot
- Gemini Search can be disabled at any time
- Results are filtered and validated by Gemini

## Benefits

- **Real-time Information**: Access to current events and latest data
- **Fact Checking**: Verify information with web sources
- **Enhanced Accuracy**: Responses backed by web search when needed
- **Seamless Integration**: No need to leave the chat for searches

## Limitations

- Only available for Gemini models
- Search behavior is determined by Gemini's internal logic
- Requires active internet connection
- Results depend on Google's search index

## Troubleshooting

**Gemini Search option not visible?**
- Ensure you're using a Gemini model (Flash or Pro)
- Run the database migration if upgrading: `python scripts/add_web_search_column.py`

**No search results in response?**
- Gemini decides when search is needed based on the query
- Try queries about current events or factual information
- Ensure Gemini Search is enabled in settings

**Error messages?**
- Check your internet connection
- Verify Gemini API key is valid
- Ensure you have the latest bot version