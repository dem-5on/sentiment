import config
import logging
from telegram import Update
from monitor import UsageTracker
from ai.gemini_service import GeminiService
from scraper.news_scraper import NewsScraper
from bot.telegram_bot import TelegramNewsBot
from crypto.crypto_data import CryptoDataFetcher
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


# Initialize usage tracker
usage_tracker = UsageTracker()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and show main keyboard"""
    bot = TelegramNewsBot()

    # Add tracking

    user_id = update.effective_user.id
    username = update.effective_user.username
    usage_tracker.track_user(user_id, username)
    chat_id = update.effective_chat.id

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
    message += f"**Available Commands:**\n\n"
    
    # Main buttons
    message += f"📰 *Get News Now*\n"
    message += f"Fetch latest news immediately from all RSS feeds\n\n"
    
    message += f"🤖 *AI Summarized News*\n"
    message += f"Get AI-powered summaries of news articles\n"
    message += f"  • 📄 Individual Summaries\n"
    message += f"  • 📋 Combined Summary\n\n"
    
    message += f"💰 *Crypto Data*\n"
    message += f"Current crypto prices and Fear & Greed Index\n\n"
    
    message += f"📊 *Status*\n"
    message += f"Check bot configuration and service status\n\n"
    
    message += f"🔧 *AI Status*\n"
    message += f"Check Gemini AI service availability\n\n"
    
    message += f"❓ *Help*\n"
    message += f"Show this help menu\n\n"
    
    # Scheduled info
    message += f"**Automated Features:**\n"
    message += f"🕒 Daily news at *{config.SCHEDULE_TIME}*\n"
    message += f"🏷️ Tracking keywords: `{', '.join(config.KEYWORDS)}`\n\n"
    
    # RSS sources summary
    message += f"**News Sources:**\n"
    message += f"📡 Monitoring {len(config.RSS_FEEDS)} RSS feeds\n"
    
    # Show first few sources
    if config.SITE:
        for i, feed in enumerate(config.SITE[:3], 1):
            message += f"  {i}. {feed}"
        if len(config.SITE) > 3:
            message += f"  ... and {len(config.SITE) - 3} more sources\n"

    logging.info(f"Help command invoked by user {update.effective_user.id}")
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=bot.get_main_keyboard()
    )

async def crypto_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto data request"""
    bot = TelegramNewsBot()
    
    # Add tracking
    user_id = update.effective_user.id
    username = update.effective_user.username
    usage_tracker.track_user(user_id, username)
    usage_tracker.track_crypto_request(user_id)
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "💰 Fetching crypto prices and market data...",
        reply_markup=bot.get_main_keyboard()
    )
    
    try:
        # Fetch crypto data
        crypto_fetcher = CryptoDataFetcher()
        crypto_summary = crypto_fetcher.get_crypto_summary(config.CRYPTO_SYMBOLS)
        
        if crypto_summary:
            await bot.send_crypto_data(chat_id,crypto_summary)
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
    
    # Add tracking
    user_id = update.effective_user.id
    username = update.effective_user.username
    usage_tracker.track_user(user_id, username)
    usage_tracker.track_news_request(user_id, "manual")
    chat_id = update.effective_chat.id

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
            await bot.send_news(chat_id, news_items)
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
    elif text == "🤖 AI Summarized News":
        await ai_news_menu(update, context)
    elif text == "📄 Individual Summaries":
        await ai_individual_news(update, context)
    elif text == "📋 Combined Summary":
        await ai_combined_news(update, context)
    elif text == "⬅️ Back to Main Menu":
        await start(update, context)
    else:
        # Unknown command
        bot = TelegramNewsBot()
        await update.message.reply_text(
            "⚠️ Unknown command. Use the buttons below or type /help for available commands.",
            reply_markup=bot.get_main_keyboard()
        )


async def ai_news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle AI news menu selection"""
    bot = TelegramNewsBot()
    
    message = "🤖 *AI News Summarization*\n\n"
    message += "Choose your preferred AI summary format:\n\n"
    message += "📄 *Individual Summaries* - Each article gets detailed AI analysis\n\n"
    message += "📋 *Combined Summary* - All articles summarized together with insights"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=bot.get_ai_news_keyboard()
    )

async def ai_individual_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle individual AI news summaries"""
    # Add tracking
    user_id = update.effective_user.id
    username = update.effective_user.username
    usage_tracker.track_user(user_id, username)
    chat_id = update.effective_chat.id
    
    bot = TelegramNewsBot()
    
    await update.message.reply_text(
        "🤖 Fetching news and generating individual AI summaries... This may take a few moments.",
        reply_markup=bot.get_ai_news_keyboard()
    )
    
    try:
        # Fetch news
        scraper = NewsScraper()
        news_items = scraper.scrape_news(
            keywords=config.KEYWORDS,
            rss_feeds=config.RSS_FEEDS,
            max_results=config.MAX_NEWS_PER_KEYWORD
        )
        
        if news_items:
            # Track AI request
            service_type = "API"
            usage_tracker.track_ai_request(user_id, service_type, success=True)
            
            # Estimate token usage
            total_text_length = sum(len(item['title']) + len(item['summary']) for item in news_items)
            usage_tracker.estimate_token_usage(total_text_length, is_input=True)
            
            # Generate AI summaries
            gemini = GeminiService()
            ai_news_items = gemini.summarize_individual_articles(news_items)
            await bot.send_ai_individual_news(chat_id, ai_news_items)
        else:
            await update.message.reply_text(
                "📰 No news found matching your keywords for AI summarization.",
                reply_markup=bot.get_ai_news_keyboard()
            )
    
    except Exception as e:
        # Track failed AI request
        service_type = "API"
        usage_tracker.track_ai_request(user_id, service_type, success=False)
        
        logging.error(f"Error in AI individual news: {str(e)}")
        await update.message.reply_text(
            f"⚠️ Error generating AI summaries: {str(e)}",
            reply_markup=bot.get_ai_news_keyboard()
        )


async def ai_combined_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle combined AI news summary"""
    bot = TelegramNewsBot()
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    usage_tracker.track_user(user_id, username)
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🤖 Fetching news and generating combined AI summary... This may take a moment.",
        reply_markup=bot.get_ai_news_keyboard()
    )
    
    try:
        # Fetch news
        scraper = NewsScraper()
        news_items = scraper.scrape_news(
            keywords=config.KEYWORDS,
            rss_feeds=config.RSS_FEEDS,
            max_results=config.MAX_NEWS_PER_KEYWORD
        )
        
        if news_items:
            # Generate combined AI summary
            gemini = GeminiService()
            combined_summary = gemini.summarize_combined_articles(news_items)
            await bot.send_ai_combined_news(chat_id, news_items, combined_summary)
        else:
            await update.message.reply_text(
                "📰 No news found matching your keywords for AI summarization.",
                reply_markup=bot.get_ai_news_keyboard()
            )
    
    except Exception as e:
        logging.error(f"Error in AI combined news: {str(e)}")
        await update.message.reply_text(
            f"⚠️ Error generating combined AI summary: {str(e)}",
            reply_markup=bot.get_ai_news_keyboard()
        )

async def developer_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send usage report to developer on demand"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if user is the developer
    if str(user_id) != str(config.DEVELOPER_CHAT_ID):
        await update.message.reply_text("⚠️ This command is for developers only.")
        return
    
    try:
        # Generate the report content directly here instead of using send_daily_report
        bot = TelegramNewsBot()
        
        # Calculate stats
        total_users = len(usage_tracker.data['users']) if isinstance(usage_tracker.data['users'], list) else len(usage_tracker.data['users'])
        
        # Get yesterday's stats
        from datetime import datetime, timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_stats = usage_tracker.data['daily_stats'].get(yesterday, {
            'news_requests': 0,
            'ai_requests': 0,
            'crypto_requests': 0,
            'unique_users': []
        })
        
        # Get last 7 days stats
        week_stats = usage_tracker._get_week_stats()
        
        # Create report message
        report = f"📊 *Bot Usage Report*\n\n"
        report += f"📅 **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Overall stats
        report += f"👥 **Total Users:** {total_users}\n"
        report += f"📰 **Total News Requests:** {usage_tracker.data['total_news_requests']}\n"
        report += f"🤖 **Total AI Requests:** {usage_tracker.data['total_ai_requests']}\n"
        report += f"💰 **Total Crypto Requests:** {usage_tracker.data['total_crypto_requests']}\n\n"
        
        # Yesterday's activity
        report += f"📊 **Yesterday's Activity:**\n"
        report += f"• News requests: {yesterday_stats['news_requests']}\n"
        report += f"• AI requests: {yesterday_stats['ai_requests']}\n"
        report += f"• Crypto requests: {yesterday_stats['crypto_requests']}\n"
        report += f"• Active users: {len(yesterday_stats['unique_users'])}\n\n"
        
        # Gemini API usage
        gemini = usage_tracker.data['gemini_requests']
        report += f"🤖 **Gemini API Usage:**\n"
        report += f"• API calls: {gemini['api_calls']}\n"
        report += f"• Estimated tokens: {gemini['tokens_used']:,}\n"
        report += f"• Errors: {gemini['errors']}\n\n"
        
        # Weekly trend
        report += f"📈 **7-Day Trend:**\n"
        report += f"• Avg daily requests: {week_stats['avg_daily_requests']:.1f}\n"
        report += f"• Avg active users: {week_stats['avg_daily_users']:.1f}\n"
        report += f"• Most active day: {week_stats['most_active_day']}\n\n"
        
        report += f"🕐 **Report Time:** {datetime.now().strftime('%H:%M:%S')}"
        
        # Send report to the requesting chat
        await bot.send_message(
            chat_id=chat_id,
            text=report,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error generating report: {str(e)}")

# Add to handlers list
handlers = [
    CommandHandler('start', start),
    CommandHandler('status', status_command),
    CommandHandler('help', help_command),
    CommandHandler('news', get_news_now),
    CommandHandler('crypto', crypto_data_command),
    CommandHandler('report', developer_report),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages),
]

