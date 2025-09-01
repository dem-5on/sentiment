import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
import logging
from datetime import datetime
import schedule
from telegram.ext import Application

import config
from news_scraper import NewsScraper
from telegram_bot import TelegramNewsBot
from handlers import handlers

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsBot:
    def __init__(self):
        self.scraper = NewsScraper()
        self.telegram_bot = TelegramNewsBot()
        self.app = None
        self.scheduler = AsyncIOScheduler()
        
    async def fetch_and_send_news(self):
        """Main function to scrape and send news"""
        try:
            logger.info("Starting news fetch...")
            
            # Scrape news
            news_items = self.scraper.scrape_news(
                keywords=config.KEYWORDS,
                rss_feeds=config.RSS_FEEDS,
                max_results=config.MAX_NEWS_PER_KEYWORD
            )
            
            logger.info(f"Found {len(news_items)} news items")
            
            # Send news via Telegram
            await self.telegram_bot.send_news(news_items)
            
            logger.info("News sent successfully!")
            
        except Exception as e:
            error_msg = f"Error in news fetch: {str(e)}"
            logger.error(error_msg)
            await self.telegram_bot.send_error(error_msg)
    
    def run_scheduled_job(self):
        """Wrapper to run async function in sync context"""
        # Create a task instead of using asyncio.run()
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.fetch_and_send_news())
        else:
            asyncio.run(self.fetch_and_send_news())
    
    async def setup_telegram_bot(self):
        """Setup Telegram bot with handlers"""
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        for handler in handlers:
            self.app.add_handler(handler)
            
        # Start bot
        await self.app.initialize()
        await self.app.start()
        logger.info("Telegram bot started")
        
    async def run_bot(self):
        """Main run function"""
        try:
            # Setup Telegram bot
            await self.setup_telegram_bot()
            
            # Schedule news fetching
            schedule.every().day.at(config.SCHEDULE_TIME).do(self.run_scheduled_job)
            logger.info(f"Scheduled news delivery at {config.SCHEDULE_TIME} daily")
            
            # Send startup message
            await self.telegram_bot.send_message(
                f"🚀 News bot started!\nScheduled for {config.SCHEDULE_TIME} daily\nKeywords: {', '.join(config.KEYWORDS)}\nRSS Feeds: {len(config.RSS_FEEDS)} sources"
            )
            
            # Keep the bot running
            while True:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {str(e)}")
        finally:
            if self.app:
                await self.app.stop()
                await self.app.shutdown()

def main():
    """Entry point"""
    # Validate configuration
    if not all([config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID]):
        logger.error("Missing required Telegram environment variables!")
        return
        
    if not config.KEYWORDS:
        logger.error("No keywords specified!")
        return
        
    if not config.RSS_FEEDS:
        logger.error("No RSS feeds specified!")
        return
    
    # Run bot
    bot = NewsBot()
    asyncio.run(bot.run_bot())

if __name__ == "__main__":
    main()