import config
import logging
from telegram.constants import ParseMode
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class TelegramNewsBot:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.chat_id = config.TELEGRAM_CHAT_ID
        
    def get_main_keyboard(self):
        """Create the main reply keyboard with buttons"""
        keyboard = [
            [KeyboardButton("📰 Get News Now"),  KeyboardButton("💰 Crypto Data")],
            [KeyboardButton("📊 Status"), KeyboardButton("❓ Help")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        
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
            # Small delay between messages to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)
            
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
            
    async def send_message(self, text, parse_mode=None, reply_markup=None):
        """Send simple text message"""
        try:
            # Use main keyboard if no reply_markup specified
            if reply_markup is None:
                reply_markup = self.get_main_keyboard()
                
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            
    async def send_error(self, error_message):
        """Send error notification"""
        message = f"⚠️ *News Bot Error*\n\n{error_message}"
        await self.send_message(message, parse_mode=ParseMode.MARKDOWN)

    async def send_crypto_data(self, crypto_summary):
        """Send crypto prices and fear & greed index"""
        try:
            if not crypto_summary:
                await self.send_message("❌ Unable to fetch crypto data at the moment.")
                return
            
            message = "💰 *Crypto Market Update*\n\n"
            
            # Add prices
            if crypto_summary['prices']:
                message += "📊 *Current Prices:*\n"
                for symbol, price in crypto_summary['prices'].items():
                    # Format price nicely
                    if price >= 1:
                        formatted_price = f"${price:,.2f}"
                    else:
                        formatted_price = f"${price:.6f}"
                    message += f"• {symbol}: `{formatted_price}`\n"
                message += "\n"
            
            # Add Fear & Greed Index
            if crypto_summary['fear_greed']:
                fg = crypto_summary['fear_greed']
                
                # Add emoji based on classification
                classification = fg['classification'].lower()
                if 'extreme fear' in classification:
                    emoji = "😨"
                elif 'fear' in classification:
                    emoji = "😰"
                elif 'neutral' in classification:
                    emoji = "😐"
                elif 'greed' in classification:
                    emoji = "🤑"
                elif 'extreme greed' in classification:
                    emoji = "🚀"
                else:
                    emoji = "📊"
                
                message += f"📈 *Fear & Greed Index:*\n"
                message += f"{emoji} {fg['value']}/100 - _{fg['classification'].title()}_\n\n"
            
            message += f"🕒 Updated: {crypto_summary['timestamp'].strftime('%H:%M:%S')}"
            
            await self.send_message(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logging.error(f"Error sending crypto data: {str(e)}")
            await self.send_message("❌ Error formatting crypto data.")