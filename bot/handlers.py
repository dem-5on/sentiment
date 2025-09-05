import config
import logging
from telegram import Update
from scraper.news_scraper import NewsScraper
from bot.telegram_bot import TelegramNewsBot
from crypto.crypto_data import CryptoDataFetcher
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and show main keyboard"""
    bot = TelegramNewsBot()
    
    message = f"🤖 *Welcome to News Bot!*\n\n"
    message += f"📅 Scheduled time: {config.SCHEDULE_TIME}\n\n"
    message += f"🔍 Keywords: {', '.join(config.KEYWORDS)}\n\n"
    message += f"🌐 RSS Sources: {len(config.RSS_FEEDS)} feeds\n\n"
    message += "Use the buttons below to interact with the bot!"
    
    logging.info(f"Start command invoked by user {update.effective_user.id}")
    logging.info(f"Start command response: {message}")
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=bot.get_main_keyboard()
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle status command"""
    bot = TelegramNewsBot()
    
    message = f"📊 *Bot Status*\n\n"
    message += f"⏰ Schedule: {config.SCHEDULE_TIME} daily\n\n"
    message += f"🏷️ Keywords: `{', '.join(config.KEYWORDS)}`\n\n"
    message += f"📰 Max news per keyword: {config.MAX_NEWS_PER_KEYWORD}\n\n"
    message += f"🕒 Cache duration: {config.NEWS_CACHE_HOURS} hours\n\n"
    message += f"📈 Fear & Greed Index: Enabled\n\n"

    # Add crypto symbols
    if hasattr(config, 'CRYPTO_SYMBOLS') and config.CRYPTO_SYMBOLS:
        message += f"💰 Crypto Symbols: \n`{', '.join(config.CRYPTO_SYMBOLS)}`\n\n"
    else:
        message += f"💰 Crypto Symbols: Not configured\n"
    
    for feed in config.SITE:
        message += f"📡 RSS Feed: *{feed}*\n\n"
    message += f"✅ Status: Running & Ready"
    
    logging.info(f"Status command invoked by user {update.effective_user.id}")
    logging.info(f"Status command response: {message}")
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=bot.get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help command"""
    bot = TelegramNewsBot()
    
    message = f"🆘 *News Bot Help*\n\n"
    message += f"Available Commands:\n\n"
    message += f"📊 *Status* - Check bot configuration and current settings\n\n"
    message += f"📰 *Get News Now* - Fetch latest news immediately from all RSS feeds\n\n"
    message += f"🔄 *Restart Bot* - Instructions to restart the bot service\n\n"
    message += f"❓ *Help* - Show this help menu\n\n"
    message += f"🕒 The bot automatically sends news at *{config.SCHEDULE_TIME}* daily based on your keywords.\n\n"
    message += f"*Current Keywords:* {', '.join(config.KEYWORDS)}\n"
    message += f"*RSS Sources:* {len(config.RSS_FEEDS)} feeds monitored\n"
    for feed in config.SITE:
        message += f"📡 Sources: *{feed}*\n\n"
    
    logging.info(f"Help command invoked by user {update.effective_user.id}")
    logging.info(f"Help command response: {message}")
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=bot.get_main_keyboard()
    )

async def crypto_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto data request"""
    bot = TelegramNewsBot()
    
    await update.message.reply_text(
        "💰 Fetching crypto prices and market data...",
        reply_markup=bot.get_main_keyboard()
    )
    
    try:
        # Fetch crypto data
        crypto_fetcher = CryptoDataFetcher()
        crypto_summary = crypto_fetcher.get_crypto_summary(config.CRYPTO_SYMBOLS)
        
        if crypto_summary:
            await bot.send_crypto_data(crypto_summary)
        else:
            await update.message.reply_text(
                "❌ Unable to fetch crypto data at the moment. Please try again later.",
                reply_markup=bot.get_main_keyboard()
            )
    
        logging.info(f"Crypto data command invoked by user {update.effective_user.id}")
        logging.info(f"Crypto data response: {crypto_summary}")

    except Exception as e:
        logging.error(f"Error in crypto data fetch: {str(e)}")
        await update.message.reply_text(
            f"⚠️ Error fetching crypto data: {str(e)}",
            reply_markup=bot.get_main_keyboard()
        )

async def get_news_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle immediate news request"""
    bot = TelegramNewsBot()
    
    await update.message.reply_text(
        "🔍 Fetching latest news from all RSS feeds... This may take a moment.",
        reply_markup=bot.get_main_keyboard()
    )
    
    try:
        # Fetch news immediately
        scraper = NewsScraper()
        news_items = scraper.scrape_news(
            keywords=config.KEYWORDS,
            rss_feeds=config.RSS_FEEDS,
            max_results=config.MAX_NEWS_PER_KEYWORD
        )
        
        if news_items:
            await bot.send_news(news_items)
        else:
            await update.message.reply_text(
                "📰 No news found matching your keywords at the moment.\n\nTried keywords: " + ", ".join(config.KEYWORDS),
                reply_markup=bot.get_main_keyboard()
            )
    
        logging.info(f"News fetch command invoked by user {update.effective_user.id}")
        logging.info(f"News fetch found {len(news_items)} items")
    except Exception as e:
        logging.error(f"Error in manual news fetch: {str(e)}")
        await update.message.reply_text(
            f"⚠️ Error fetching news: {str(e)}",
            reply_markup=bot.get_main_keyboard()
        )


async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from markup buttons"""
    text = update.message.text
    
    if text == "📊 Status":
        await status_command(update, context)
    elif text == "❓ Help":
        await help_command(update, context)
    elif text == "💰 Crypto Data":
        await crypto_data_command(update, context)
    elif text == "📰 Get News Now":
        await get_news_now(update, context)
    else:
        # Unknown command
        bot = TelegramNewsBot()
        await update.message.reply_text(
            "❌ Unknown command. Use the buttons below or type /help for available commands.",
            reply_markup=bot.get_main_keyboard()
        )

# Handler list for easy import
handlers = [
    CommandHandler('start', start),
    CommandHandler('status', status_command),
    CommandHandler('help', help_command),
    CommandHandler('news', get_news_now),
    CommandHandler('crypto', crypto_data_command),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages),
]