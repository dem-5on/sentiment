import asyncio
import schedule
import logging
import threading
import time
from telegram.ext import Application
import config
from scraper.news_scraper import NewsScraper
from bot.telegram_bot import TelegramNewsBot
from bot.handlers import handlers

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
        self.running = True
        
    async def fetch_and_send_news(self):
        """Main function to scrape and send news"""
        try:
            logger.info("Starting scheduled news fetch...")
            
            # Scrape news
            news_items = self.scraper.scrape_news(
                keywords=config.KEYWORDS,
                rss_feeds=config.RSS_FEEDS,
                max_results=config.MAX_NEWS_PER_KEYWORD
            )
            
            logger.info(f"Found {len(news_items)} news items")
            
            # Send news via Telegram
            await self.telegram_bot.send_news(news_items)
            
            logger.info("Scheduled news sent successfully!")
            
        except Exception as e:
            error_msg = f"Error in scheduled news fetch: {str(e)}"
            logger.error(error_msg)
            await self.telegram_bot.send_error(error_msg)
    
    def run_scheduled_job(self):
        """Wrapper to run async function in sync context for scheduler"""
        try:
            # Use asyncio.run instead of creating new event loop
            asyncio.run(self.fetch_and_send_news())
        except Exception as e:
            logger.error(f"Error in scheduled job wrapper: {str(e)}")


    def schedule_worker(self):
        """Worker thread for handling scheduled jobs"""
        schedule.every().day.at(config.SCHEDULE_TIME).do(self.run_scheduled_job)
        logger.info(f"Scheduled news delivery at {config.SCHEDULE_TIME} daily")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    async def setup_telegram_bot(self):
        """Setup Telegram bot with handlers"""
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        for handler in handlers:
            self.app.add_handler(handler)
            
        logger.info("Telegram bot handlers added")
        return self.app
        
    async def run_bot(self):
        """Main run function"""
        try:
            # Setup Telegram bot
            self.app = await self.setup_telegram_bot()
            
            # Start scheduler in separate thread
            scheduler_thread = threading.Thread(target=self.schedule_worker, daemon=True)
            scheduler_thread.start()
            
            # Send startup message
            await self.telegram_bot.send_message(
                f"🚀 *News Bot Started Successfully!*\n\n"
                f"⏰ Scheduled for: {config.SCHEDULE_TIME} daily\n\n"
                f"🏷️ Keywords: {', '.join(config.KEYWORDS)}\n\n"
                f"📡 RSS Feeds: {len(config.RSS_FEEDS)} sources\n\n"
                f"📰 Max news per keyword: {config.MAX_NEWS_PER_KEYWORD}\n\n"
                f"✅ Bot is ready to receive commands!",
                parse_mode='Markdown'
            )
            
            # Start the telegram bot polling - this will block
            logger.info("Starting Telegram bot polling...")
            async with self.app:
                await self.app.start()
                await self.app.updater.start_polling()
                
                # Keep running until stopped
                try:
                    await asyncio.Event().wait()  # Wait indefinitely
                except asyncio.CancelledError:
                    pass
                finally:
                    await self.app.updater.stop()
                    await self.app.stop()
                    
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Bot error: {str(e)}")
            self.running = False
        finally:
            self.running = False

def main():
    """Entry point"""
    # Validate configuration
    if not all([config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID]):
        logger.error("Missing required environment variables!")
        logger.error("Required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        return
        
    if not config.KEYWORDS:
        logger.error("No keywords specified!")
        return
        
    if not config.RSS_FEEDS:
        logger.error("No RSS feeds specified!")
        return
    
    logger.info("Starting News Bot...")
    logger.info(f"Schedule: {config.SCHEDULE_TIME}")
    logger.info(f"Keywords: {config.KEYWORDS}")
    logger.info(f"RSS Feeds: {len(config.RSS_FEEDS)} sources")
    
    # Run bot
    bot = NewsBot()
    try:
        asyncio.run(bot.run_bot())
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    main()