import config
import logging
import asyncio
from telegram.constants import ParseMode
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class TelegramNewsBot:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        
    def get_main_keyboard(self):
        """Create the main reply keyboard with buttons"""
        keyboard = [
            [KeyboardButton("📰 Get News Now"), KeyboardButton("🤖 AI Summarized News")],
            [KeyboardButton("💰 Crypto Data"), KeyboardButton("📊 Status")], 
            [KeyboardButton("❓ Help")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    async def send_news(self, chat_id, news_items):
        """Send news items to Telegram chat"""
        if not news_items:
            await self.send_message(chat_id, "No news found for your keywords today.")
            return
            
        # Send header message
        header = f"📰 *Daily News Update* - {len(news_items)} articles found\n"
        header += f"Keywords: {', '.join(config.KEYWORDS)}\n\n"

        await self.send_message(chat_id, header, parse_mode=ParseMode.MARKDOWN)

        # Send each news item
        for i, news in enumerate(news_items, 1):
            await self.send_news_item(chat_id, news, i)
            # Small delay between messages to avoid rate limiting
            await asyncio.sleep(0.5)

    async def send_news_item(self, chat_id, news_item, index):
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
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logging.error(f"Error sending news item: {str(e)}")

    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        """Send simple text message"""
        try:
            # Use main keyboard if no reply_markup specified
            if reply_markup is None:
                reply_markup = self.get_main_keyboard()
                
            await self.bot.send_message(
                chat_id=chat_id,
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

    async def send_crypto_data(self, chat_id, crypto_summary):
        """Send detailed crypto market data"""
        try:
            if not crypto_summary:
                await self.send_message(chat_id, "❌ Unable to fetch crypto data at the moment.")
                return

            message = "💰 *CRYPTO DATA*\n\n"

            # Loop through each crypto symbol
            if crypto_summary.get('prices'):
                for symbol, data in crypto_summary['prices'].items():
                    price = data.get('price', 0)
                    change = data.get('change_24h_percent', 0)
                    volume = data.get('volume_24h', 0)
                    high = data.get('high_24h', 0)
                    low = data.get('low_24h', 0)

                    # Format nicely
                    message += f"*Symbol:* {data['symbol']}\n"
                    message += f"💵 Current Price: ${price:,.2f}\n"
                    message += f"📈 24h % Change: {change:+.2f}%\n"
                    message += f"📊 24h Volume: {volume:,.0f}\n"
                    message += f"🔼 24h High: ${high:,.2f}\n"
                    message += f"🔽 24h Low: ${low:,.2f}\n"
                    message += "───────────────────────\n\n"

            # Add Fear & Greed Index
            if crypto_summary.get('fear_greed'):
                fg = crypto_summary['fear_greed']
                classification = fg['classification'].title()
                value = fg['value']

                message += f"📈 *Fear & Greed Index:* {value}/100 - {classification}\n\n"

            # Add timestamp
            if "timestamp" in crypto_summary:
                message += f"🕒 Updated: {crypto_summary['timestamp'].strftime('%H:%M:%S')}"

            await self.send_message(chat_id, message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logging.error(f"Error sending crypto data: {str(e)}")
            await self.send_message(chat_id, "❌ Error formatting crypto data.")


    def get_ai_news_keyboard(self):
        """Create AI news selection keyboard"""
        keyboard = [
            [KeyboardButton("📄 Individual Summaries"), KeyboardButton("📋 Combined Summary")],
            [KeyboardButton("⬅️ Back to Main Menu")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    async def send_ai_individual_news(self, chat_id, news_items_with_ai):
        """Send individually AI-summarized news items"""
        if not news_items_with_ai:
            await self.send_message(chat_id, text="No news found for AI summarization.")
            return
            
        # Send header
        header = f"🤖 *AI Individual Summaries* - {len(news_items_with_ai)} articles\n"
        header += f"Keywords: {', '.join(config.KEYWORDS)}\n\n"

        await self.send_message(chat_id, text=header, parse_mode=ParseMode.MARKDOWN)

        # Send each AI-summarized item
        for i, news in enumerate(news_items_with_ai, 1):
            await self.send_ai_news_item(chat_id, news, i)
            await asyncio.sleep(1)  # Longer delay for AI content

    async def send_ai_combined_news(self, chat_id, news_items, combined_summary):
        """Send combined AI summary of all news"""
        if not combined_summary:
            await self.send_message(chat_id, text="Unable to generate combined AI summary.")
            return
            
        # Send header with article count
        header = f"🤖 *AI Combined Summary* - {len(news_items)} articles analyzed\n"
        header += f"Keywords: {', '.join(config.KEYWORDS)}\n\n"

        await self.send_message(chat_id, text=header, parse_mode=ParseMode.MARKDOWN)

        # Send combined summary
        message = f"{combined_summary}\n\n"
        message += f"📰 *Source Articles:*\n"
        
        # Add list of source articles
        for i, news in enumerate(news_items, 1):
            message += f"{i}. [{news['title'][:50]}...]({news['url']}) - _{news['source']}_\n"

        await self.send_message(chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

    async def send_ai_news_item(self, chat_id, news_item, index):
        """Send individual AI-summarized news item"""
        try:
            # Format message with original info + AI summary
            message = f"🤖 *{index}. {news_item['title']}*\n\n"
            
            # Add AI summary
            if news_item.get('ai_summary'):
                message += f"{news_item['ai_summary']}\n\n"
            else:
                message += f"_{news_item['summary']}_\n\n"
            
            message += f"🏷️ Keyword: _{news_item['keyword']}_\n"
            message += f"📰 Source: _{news_item['source']}_"
            
            # Create inline keyboard
            keyboard = [
                [InlineKeyboardButton("📖 Read Full Article", url=news_item['url'])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logging.error(f"Error sending AI news item: {str(e)}")