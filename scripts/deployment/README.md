# Telethon AI Bot Deployment

This directory contains Ansible scripts to deploy the Telethon AI Bot to a Debian Bookworm server.

## Prerequisites

1. **Local Machine Requirements:**
   - Ansible installed: `pip install ansible`
   - SSH access to the target server
   - SSH key authentication configured

2. **Target Server Requirements:**
   - Debian Bookworm (12) or compatible
   - Root or sudo access
   - Python 3 installed

## Setup

1. **Create Inventory File:**
   ```bash
   cp inventory.template inventory
   ```
   
   Edit `inventory` and replace with your server details:
   ```ini
   [telethon_bot]
   your-server ansible_host=YOUR_SERVER_IP ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
   ```

2. **Configure Doppler (on the server):**
   The bot uses Doppler for secrets management. You'll need to:
   - Set up Doppler project and environment
   - Configure `DOPPLER_TOKEN` on the server
   - Set `ENVIRONMENT` variable (DEV/PROD)

## Deployment

### Full Deployment
Deploy the bot to the server:
```bash
./deploy.sh
# or
./deploy.sh deploy
```

This will:
- Use the existing user (`sasidhar`) or create if not exists
- Install Python 3.11 (builds from source on Debian if needed)
- Install system dependencies
- Sync the code to `/home/sasidhar/telethon-ai-bot`
- Install Python dependencies in a virtual environment
- **Run database migrations automatically (Alembic)**
- Set up systemd service
- Configure log rotation
- Start the bot

### Service Management

**Check Status:**
```bash
./deploy.sh status
```

**Restart Bot:**
```bash
./deploy.sh restart
```

**Stop Bot:**
```bash
./deploy.sh stop
```

**Start Bot:**
```bash
./deploy.sh start
```

**View Logs:**
```bash
./deploy.sh logs
```

## File Locations on Server

- **Bot Code:** `/home/sasidhar/telethon-ai-bot/`
- **Logs:** `/var/log/telethon-ai-bot/`
  - `bot.log` - Standard output
  - `error.log` - Error output
- **Image Storage:** `/home/sasidhar/.telethon-bot-storage/`
- **Database:** `/home/sasidhar/telethon-ai-bot/bot_database.db`
- **Service File:** `/etc/systemd/system/telethon-ai-bot.service`

## Log Rotation

Logs are automatically rotated daily with:
- 14 days retention
- Compression enabled
- Configuration at `/etc/logrotate.d/telethon-ai-bot`

## Updating the Bot

To deploy code changes:
```bash
# Make your changes locally
git commit -am "Your changes"

# Deploy to server
./deploy.sh

# The bot will automatically restart with new code
```

## Post-Deployment Verification

1. **Check Database Migrations:**
   ```bash
   # Verify migrations were applied
   ansible telethon_bot -i inventory -m shell -a "cd /home/sasidhar/telethon-ai-bot && ./venv/bin/alembic current" --become --become-user=sasidhar
   ```

2. **Authenticate the Bot (first time only):**
   ```bash
   # SSH to server and run the bot manually to authenticate
   ssh your-server
   sudo -u sasidhar /home/sasidhar/telethon-ai-bot/venv/bin/python /home/sasidhar/telethon-ai-bot/main.py
   ```

3. **Set up Doppler (if not already done):**
   ```bash
   # On the server
   doppler login
   doppler setup
   ```

## Troubleshooting

1. **Check Service Status:**
   ```bash
   ./deploy.sh status
   ```

2. **View Logs:**
   ```bash
   ./deploy.sh logs
   
   # Or SSH to server and check:
   tail -f /var/log/telethon-ai-bot/bot.log
   tail -f /var/log/telethon-ai-bot/error.log
   ```

3. **Check Systemd Journal:**
   ```bash
   ansible telethon_bot -i inventory -m shell -a "journalctl -u telethon-ai-bot -n 50" --become
   ```

4. **Manual Service Control (on server):**
   ```bash
   sudo systemctl status telethon-ai-bot
   sudo systemctl restart telethon-ai-bot
   sudo journalctl -u telethon-ai-bot -f
   ```

## Security Notes

- The bot runs as user `sasidhar` with appropriate permissions
- SystemD security features are enabled (NoNewPrivileges, ProtectSystem)
- File storage is restricted to specific directories
- Resource limits are applied (1GB memory, 80% CPU)

## Manual Setup (if needed)

If you need to set up Doppler manually on the server:
```bash
# Install Doppler CLI
curl -Ls https://cli.doppler.com/install.sh | sh

# Login to Doppler
doppler login

# Set up the project
cd /home/sasidhar/telethon-ai-bot
doppler setup

# Set environment variables for the service
echo "DOPPLER_TOKEN=your_token_here" >> /etc/environment
echo "ENVIRONMENT=PROD" >> /etc/environment