from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import config
import logging

class TelegramNewsBot:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.chat_id = config.TELEGRAM_CHAT_ID
        
    async def send_news(self, news_items):
        """Send news items to Telegram chat"""
        if not news_items:
            await self.send_message("No news found for your keywords today.")
            return
            
        # Send header message
        header = f"📰 *Daily News Update* - {len(news_items)} articles found\n"
        header += f"Keywords: {', '.join(config.KEYWORDS)}\n\n"
        
        await self.send_message(header, parse_mode=ParseMode.MARKDOWN)
        
        # Send each news item
        for i, news in enumerate(news_items, 1):
            await self.send_news_item(news, i)
            
    async def send_news_item(self, news_item, index):
        """Send individual news item with Read More button"""
        try:
            # Format message
            message = f"*{index}. {news_item['title']}*\n\n"
            message += f"{news_item['summary']}\n\n"
            message += f"🏷️ Keyword: _{news_item['keyword']}_\n"
            message += f"📰 Source: _{news_item['source']}_"
            
            # Create inline keyboard for "Read More" button
            keyboard = [
                [InlineKeyboardButton("📖 Read More", url=news_item['url'])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logging.error(f"Error sending news item: {str(e)}")
            
    async def send_message(self, text, parse_mode=None):
        """Send simple text message"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode
            )
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            
    async def send_error(self, error_message):
        """Send error notification"""
        message = f"❌ *News Bot Error*\n\n{error_message}"
        await self.send_message(message, parse_mode=ParseMode.MARKDOWN)