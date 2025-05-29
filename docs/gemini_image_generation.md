# Gemini Image Generation Feature

This document describes the image generation capabilities added to the Telethon AI Bot for Gemini models.

## Overview

The bot now supports two image generation models from Google:

1. **Gemini 2.0 Flash (Image Gen)** - Uses the `gemini-2.0-flash-preview-image-generation` model that can generate images as part of its response
2. **Imagen 3** - Uses the specialized `imagen-3.0-generate-002` model for high-quality image generation

## How It Works

### Gemini 2.0 Flash Image Generation

When using the Gemini 2.0 Flash (Image Gen) model, the bot can generate and edit images based on prompts within the conversation. The model supports multiple image interaction modes:

**Supported Modes**:
- **Text to image**: Generate images from text descriptions
- **Image editing**: Modify existing images based on text instructions
- **Multi-turn conversations**: Continue editing images conversationally

Example prompts:
- Text to image: "Create a 3D rendered image of a pig with wings"
- Image editing: Send an image and say "Turn this car into a convertible"
- Multi-turn: After generating an image, say "Now change the color to yellow"

### Imagen 3

Imagen 3 is a specialized image generation model that focuses solely on creating high-quality images from text prompts. When this model is selected, only your current message will be used as the image generation prompt (conversation history is not used).

## Usage

1. **Select the Model**: Use the `/settings` command and navigate to "Change Model" → "Google" to select either:
   - 🎨 Gemini 2.0 Flash (Image Gen)
   - 🖼️ Imagen 3

2. **Send Your Prompt**: Simply send a message describing what you want to generate

3. **Receive Images**: The bot will generate and send the image(s) directly in the chat

## Technical Implementation

### Response Format

Generated images are saved to temporary files and sent as Telegram photo messages. The bot uses a special internal format `[IMAGE_GENERATED:path1|path2|...]` to track generated images.

### File Management

- Images are saved to temporary directories
- Files are automatically cleaned up after being sent
- Supports multiple images in a single response

### Model Integration

The implementation extends the existing Gemini client to:
- Support image response modalities for the Flash model
- Handle the specialized Imagen 3 API
- Process and save generated images
- Return appropriate responses to the bot handler

## Limitations

- Image generation requires a valid Gemini API key
- Generated images are temporary and not stored permanently
- Image generation may take longer than text responses
- API rate limits apply based on your Google Cloud project
- Web search is not available when using image generation models (automatically disabled)
- Thinking mode is not available for image generation models
- Imagen 3 only processes the current message, not conversation history
- For best performance, use English, Spanish, Japanese, Chinese, or Hindi languages

## Error Handling

If image generation fails, the bot will:
- Return an error message explaining the issue
- Fall back to text-only responses when possible
- Log detailed errors for debugging