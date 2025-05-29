#!/usr/bin/env python3
"""
Setup script for Telethon AI Bot
Helps users configure the bot with required credentials
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from user input"""
    print("=== Telethon AI Bot Setup ===\n")
    
    if Path(".env").exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    print("\n📱 Telegram Configuration")
    print("Get these from https://my.telegram.org")
    api_id = input("Enter your Telegram API ID: ").strip()
    api_hash = input("Enter your Telegram API Hash: ").strip()
    
    print("\nGet bot token from @BotFather on Telegram")
    bot_token = input("Enter your Bot Token: ").strip()
    
    print("\n🤖 Gemini API Configuration")
    print("Get API key from https://makersuite.google.com/app/apikey")
    gemini_key = input("Enter your Gemini API Key: ").strip()
    
    print("\n👥 Whitelist Configuration")
    print("Get user IDs from @userinfobot on Telegram")
    print("Enter comma-separated user IDs (e.g., 123456789,987654321)")
    whitelist = input("Whitelisted User IDs: ").strip()
    
    # Create .env content
    env_content = f"""# Telegram Bot Configuration
API_ID={api_id}
API_HASH={api_hash}
BOT_TOKEN={bot_token}

# Gemini API Configuration
GEMINI_API_KEY={gemini_key}

# Whitelist (comma-separated user IDs)
WHITELISTED_USERS={whitelist}

# Database
DATABASE_URL=sqlite+aiosqlite:///bot_database.db
"""
    
    # Write .env file
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("\n✅ .env file created successfully!")
    print("\nYou can now run the bot with: python main.py")

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Your version: Python {sys.version}")
        sys.exit(1)

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")

def main():
    """Main setup function"""
    check_python_version()
    
    print("Welcome to Telethon AI Bot Setup!\n")
    
    # Check if requirements are installed
    try:
        import telethon
        import google.generativeai
        deps_installed = True
    except ImportError:
        deps_installed = False
    
    if not deps_installed:
        response = input("Dependencies not installed. Install now? (Y/n): ")
        if response.lower() != 'n':
            install_dependencies()
    
    # Create .env file
    response = input("\nCreate .env configuration file? (Y/n): ")
    if response.lower() != 'n':
        create_env_file()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Make sure your .env file is properly configured")
    print("2. Run the bot with: python main.py")
    print("3. Start chatting with your bot on Telegram!")

if __name__ == "__main__":
    main()