import asyncio
import schedule
import logging
import threading
import time
from datetime import datetime, timedelta
from telegram.ext import Application
import config
from scraper.news_scraper import NewsScraper
from bot.telegram_bot import TelegramNewsBot
from bot.handlers import handlers
from monitor import UsageTracker

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
        self.usage_tracker = UsageTracker()
        self.app = None
        self.running = True
        

    async def send_daily_usage_report(self):
        """Send daily usage report if needed"""
        try:
            if self.usage_tracker.should_send_report():
                await self.usage_tracker.send_daily_report()
                logging.info("Daily usage report check completed")
        except Exception as e:
            logging.error(f"Error in daily usage report: {str(e)}")
            await self.telegram_bot.send_error(f"Error in daily usage report: {str(e)}")

    async def fetch_and_send_news(self):
        """Main function to scrape and send news to all users"""
        try:
            logger.info("Starting scheduled news fetch...")
            
            # Get all user chat IDs
            user_chat_ids = self.usage_tracker.get_all_user_chat_ids()
            if not user_chat_ids:
                logger.warning("No users found to send scheduled news")
                return
            
            # Scrape news
            news_items = self.scraper.scrape_news(
                keywords=config.KEYWORDS,
                rss_feeds=config.RSS_FEEDS,
                max_results=config.MAX_NEWS_PER_KEYWORD
            )
            
            logger.info(f"Found {len(news_items)} news items")
            logger.info(f"Sending to {len(user_chat_ids)} users")
            
            # Send news to all users
            successful_sends = 0
            failed_sends = 0
            
            for chat_id in user_chat_ids:
                try:
                    await self.telegram_bot.send_news(chat_id, news_items)
                    successful_sends += 1
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to send news to user {chat_id}: {str(e)}")
                    failed_sends += 1
            
            logger.info(f"Scheduled news sent! Success: {successful_sends}, Failed: {failed_sends}")
        except Exception as e:
            logger.error(f"Error during scheduled news fetch: {str(e)}")
        
    def run_scheduled_job(self):
        """Wrapper to run async function in sync context for scheduler"""
        try:
            # Use asyncio.run instead of creating new event loop
            asyncio.run(self.fetch_and_send_news())
        except Exception as e:
            logger.error(f"Error in scheduled job wrapper: {str(e)}")


    # Modify the schedule_worker method to include usage report
    def schedule_worker(self):
        """Worker thread for handling scheduled jobs"""
        schedule.every().day.at(config.SCHEDULE_TIME).do(self.run_scheduled_job)
        
        # Add daily usage report at a different time (e.g., 30 minutes after news)
        report_time = self._get_report_time()
        schedule.every().day.at(report_time).do(self.run_usage_report)
        
        logger.info(f"Scheduled news delivery at {config.SCHEDULE_TIME} daily")
        logger.info(f"Scheduled usage reports at {report_time} daily")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _get_report_time(self):
        """Get report time (30 minutes after news time)"""
        try:
            news_time = datetime.strptime(config.SCHEDULE_TIME, '%H:%M')
            report_time = news_time + timedelta(minutes=30)
            return report_time.strftime('%H:%M')
        except:
            return "08:30"  # Fallback time
        
    
    def run_usage_report(self):
        """Wrapper to run async usage report function"""
        try:
            asyncio.run(self.send_daily_usage_report())
        except Exception as e:
            logger.error(f"Error in usage report wrapper: {str(e)}")

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
                chat_id=config.DEVELOPER_CHAT_ID,
                text=
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