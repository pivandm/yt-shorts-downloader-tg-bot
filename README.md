# Telegram YouTube Shorts Downloader Bot

Async Telegram bot that downloads YouTube Shorts in 720p.

## Quick Deploy on VPS

```bash
# Clone repository
git clone https://github.com/yourusername/telegram-yt-bot.git
cd telegram-yt-bot

# Setup environment
cp .env.example .env
nano .env  # Add your BOT_TOKEN

# Run with Docker
docker-compose up -d

# Check logs
docker-compose logs -f