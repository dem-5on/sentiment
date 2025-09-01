# Telegram News Bot 🤖

A Docker-containerized Telegram bot that automatically sends daily news updates based on your keywords from RSS feeds.

## Features ✨

- 📰 **RSS-based news scraping** (fast and reliable)
- ⏰ **Scheduled daily delivery** at your preferred time
- 🏷️ **Keyword filtering** (bitcoin, gold, crypto, etc.)
- 🔘 **Interactive buttons** for "Read More" links
- 🐳 **Fully containerized** with Docker
- 📊 **Comprehensive logging**

## Quick Start 🚀

### 1. Clone & Setup
```bash
git clone <your-repo>
cd telegram-news-bot
```

### 2. Configure Environment
Create your `.env` file:
```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# News Configuration
KEYWORDS=bitcoin,gold,ethereum,crypto,stocks
RSS_FEEDS=https://cointelegraph.com/rss,https://www.coindesk.com/arc/outboundfeeds/rss/,https://news.bitcoin.com/feed/
SCHEDULE_TIME=08:00

# Optional
MAX_NEWS_PER_KEYWORD=3
NEWS_CACHE_HOURS=24
```

### 3. Run with Docker
```bash
# Make build script executable
chmod +x build.sh

# Build and start
./build.sh
```

## Manual Docker Commands 🔧

### Build & Run
```bash
# Build the image
docker-compose build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Development
```bash
# Run locally (without Docker)
pip install -r requirements.txt
python main.py

# Get your Telegram Chat ID
python get_chat_id.py
```

## Configuration 📝

### Getting API Keys

1. **Telegram Bot Token**: 
   - Message `@BotFather` on Telegram
   - Use `/newbot` command
   - Copy the token

2. **Telegram Chat ID**:
   - Run `python get_chat_id.py`
   - Send a message to your bot
   - Copy the Chat ID from logs

### RSS Feeds
The bot uses RSS feeds for fast, reliable news:

**Crypto News:**
- CoinTelegraph: `https://cointelegraph.com/rss`
- CoinDesk: `https://www.coindesk.com/arc/outboundfeeds/rss/`
- Bitcoin.com: `https://news.bitcoin.com/feed/`

**General News:**
- BBC: `https://feeds.bbci.co.uk/news/rss.xml`
- Yahoo Finance: `https://feeds.finance.yahoo.com/rss/2.0/headline`

## Project Structure 📁

```
news_bot/
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Docker Compose setup
├── requirements.txt        # Python dependencies
├── main.py                # Main application
├── config.py              # Configuration loader
├── news_scraper.py        # RSS scraping logic
├── telegram_bot.py        # Bot interface
├── handlers.py            # Telegram commands
├── .env                   # Your configuration
├── logs/                  # Application logs
└── build.sh               # Build script
```

## Commands 🎮

Your bot supports these Telegram commands:
- `/start` - Start the bot and see configuration
- `/status` - Check bot status and settings
- `/help` - Show help message

## Monitoring 📊

```bash
# View real-time logs
docker-compose logs -f

# Check container status
docker-compose ps

# View resource usage
docker stats telegram-news-bot
```

## Troubleshooting 🔧

**Bot not starting?**
```bash
# Check logs
docker-compose logs

# Restart container
docker-compose restart
```

**No news received?**
- Check your keywords match news content
- Verify RSS feeds are working
- Check scheduled time format (24-hour: `08:00`)

**"Chat not found" error?**
- Verify your `TELEGRAM_CHAT_ID` is correct
- Use `get_chat_id.py` to get the right ID

## License 📄

MIT License - feel free to modify and use!