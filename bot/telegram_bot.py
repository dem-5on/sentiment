import config
import logging
from telegram.constants import ParseMode
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup


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
        header = f"📰 *Daily News Update*\n\n {len(news_items)} articles found\n"
        header += f"Keywords: {', '.join(config.KEYWORDS)}\n\n"
        
        await self.send_message(header, parse_mode=ParseMode.MARKDOWN)
        
        # Send each news item
        for i, news in enumerate(news_items, 1):
            await self.send_news_item(news, i)
            # Small delay between messages to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)
            
    async def send_news_item(self, news_item, index):
        """Send individual news item as photo with caption or text message"""
        try:
            # Create caption for photo or message text
            caption = self._format_news_caption(news_item, index)
            
            # Create inline keyboard for "Read More" button
            keyboard = [
                [InlineKeyboardButton("📖 Read More", url=news_item['url'])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Try to send as photo if image is available
            if news_item.get('image_url'):
                success = await self._send_news_with_image(
                    news_item, caption, reply_markup
                )
                if success:
                    return
            
            # Fallback to text message
            await self._send_news_as_text(caption, reply_markup)
            
        except Exception as e:
            logging.error(f"Error sending news item: {str(e)}")
    
    async def _send_news_with_image(self, news_item, caption, reply_markup):
        """Try to send news as photo with caption"""
        try:
            # Send photo directly from URL (no validation)
            await self.bot.send_photo(
                chat_id=self.chat_id,
                photo=news_item['image_url'],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            logging.info(f"Sent news with image: {news_item['title'][:50]}...")
            return True
            
        except Exception as e:
            logging.error(f"Error sending photo: {str(e)}")
            return False
    
    async def _send_news_as_text(self, caption, reply_markup):
        """Send news as text message (fallback)"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Error sending text message: {str(e)}")
    
    def _format_news_caption(self, news_item, index):
        """Format news item as caption (max 1024 chars for Telegram)"""
        title = news_item['title']
        summary = news_item['summary']
        keyword = news_item['keyword']
        source = news_item['source']
        
        # Start with title and summary
        caption = f"*{index}. {title}*\n\n{summary}\n\n"
        caption += f"🏷️ _{keyword}_ • 📰 _{source}_"
        
        # Telegram caption limit is 1024 characters
        if len(caption) > 1020:
            # Truncate summary to fit
            max_summary_len = 1020 - len(f"*{index}. {title}*\n\n\n\n🏷️ _{keyword}_ • 📰 _{source}_") - 3
            if max_summary_len > 50:
                truncated_summary = summary[:max_summary_len] + "..."
                caption = f"*{index}. {title}*\n\n{truncated_summary}\n\n"
                caption += f"🏷️ _{keyword}_ • 📰 _{source}_"
            else:
                # If still too long, truncate title too
                max_title_len = 200
                truncated_title = title[:max_title_len] + "..." if len(title) > max_title_len else title
                caption = f"*{index}. {truncated_title}*\n\n"
                caption += f"🏷️ _{keyword}_ • 📰 _{source}_"
        
        return caption
            
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