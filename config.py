import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# News Configuration
KEYWORDS = os.getenv('KEYWORDS', '').split(',')
RSS_FEEDS = os.getenv('RSS_FEEDS', '').split(',')
SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '08:00')

# Optional Configuration
MAX_NEWS_PER_KEYWORD = int(os.getenv('MAX_NEWS_PER_KEYWORD', 3))
NEWS_CACHE_HOURS = int(os.getenv('NEWS_CACHE_HOURS', 24))

# Clean up empty strings from lists
KEYWORDS = [k.strip() for k in KEYWORDS if k.strip()]
RSS_FEEDS = [f.strip() for f in RSS_FEEDS if f.strip()]