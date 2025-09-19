import config
import logging
from telegram import Update
from monitor import UsageTracker
from ai.gemini_service import GeminiService
from scraper.news_scraper import NewsScraper
from bot.telegram_bot import TelegramNewsBot
from crypto.crypto_data import CryptoDataFetcher
from database.database_service import DatabaseService
from utils.url_normalize import normalize_rss_url, is_valid_rss_feed
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters


# Initialize usage tracker
usage_tracker = UsageTracker()

WAITING_FOR_ASSET = "waiting_for_asset"
WAITING_FOR_SOURCE = "waiting_for_source"
WAITING_FOR_REMOVE_ASSET = "waiting_for_remove_asset"
WAITING_FOR_REMOVE_SOURCE = "waiting_for_remove_source"


def get_user_settings(user_id: int) -> dict:
    """Get user settings from database with fallback to defaults"""
    try:
        with DatabaseService() as db:
            assets = db.get_user_assets(str(user_id))
            news_sources = db.get_user_news_sources(str(user_id))
            return {
                'assets': assets or config.CRYPTO_SYMBOLS[:3],
                'news_sources': news_sources or config.RSS_FEEDS[:3]
            }
    except Exception as e:
        logging.error(f"Error getting user settings: {str(e)}")
        return {
            'assets': config.CRYPTO_SYMBOLS[:3],
            'news_sources': config.RSS_FEEDS[:3]
        }

def update_user_settings(user_id: int, assets: list = None, news_sources: list = None) -> bool:
    """Update user settings in database"""
    try:
        with DatabaseService() as db:
            if assets is not None:
                for asset in assets:
                    db.add_user_asset(str(user_id), asset)
            if news_sources is not None:
                for source in news_sources:
                    db.add_news_source(str(user_id), source)
            return True
    except Exception as e:
        logging.error(f"Error updating user settings: {str(e)}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and show main keyboard"""
    bot = TelegramNewsBot()

    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id

    logging.info(f"Start command received from user {user_id} ({username})")

    # Add user to both database and usage tracker
    try:
        with DatabaseService() as db:
            logging.info(f"Attempting to add user to database: {user_id}")
            user = db.get_or_create_user(str(user_id), username)
            logging.info(f"Successfully processed user in database: {user_id}")
    except Exception as e:
        logging.error(f"Database error in start command: {str(e)}", exc_info=True)
    
    # Fallback tracking
    usage_tracker.track_user(user_id, username)

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
    
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Update user in database
    try:
        with DatabaseService() as db:
            db.get_or_create_user(str(user_id), username)
    except Exception as e:
        logging.error(f"Database error in status command: {str(e)}")
    
    # Get user settings
    user_settings = get_user_settings(user_id)
    
    message = f"📊 *Bot Status*\n\n"
    message += f"⏰ Schedule: {config.SCHEDULE_TIME} daily\n\n"
    message += f"🏷️ Keywords: `{', '.join(config.KEYWORDS)}`\n\n"
    message += f"📰 Max news per keyword: {config.MAX_NEWS_PER_KEYWORD}\n\n"
    message += f"🕒 Cache duration: {config.NEWS_CACHE_HOURS} hours\n\n"
    message += f"📈 Fear & Greed Index: Enabled\n\n"
    
    # Add user-specific settings
    message += f"💼 *Your Settings:*\n"
    message += f"• Tracked Crypto: `{', '.join(user_settings['assets'])}`\n"
    message += f"• News Sources: {len(user_settings['news_sources'])} active feeds\n\n"

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
    chat_id = update.effective_chat.id
    
    # Get user's preferred assets
    user_settings = get_user_settings(user_id)
    crypto_symbols = user_settings['assets'] if user_settings['assets'] else config.CRYPTO_SYMBOLS
    
    # Track the request
    usage_tracker.track_user(user_id, username)
    usage_tracker.track_crypto_request(user_id)

    await update.message.reply_text(
        "💰 Fetching crypto prices and market data...",
        reply_markup=bot.get_main_keyboard()
    )
    
    try:
        # Fetch crypto data
        crypto_fetcher = CryptoDataFetcher()
        crypto_summary = crypto_fetcher.get_crypto_summary(crypto_symbols)
        
        if crypto_summary:
            # Update user data in database
            try:
                with DatabaseService() as db:
                    db.get_or_create_user(str(user_id), username)
            except Exception as e:
                logging.error(f"Database error in crypto command: {str(e)}")
            
            await bot.send_crypto_data(chat_id, crypto_summary)
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
    chat_id = update.effective_chat.id
    
    # Get user's preferred sources
    user_settings = get_user_settings(user_id)
    rss_feeds = user_settings['news_sources'] if user_settings['news_sources'] else config.RSS_FEEDS
    
    # Track the request
    usage_tracker.track_user(user_id, username)
    usage_tracker.track_news_request(user_id, "manual")

    await update.message.reply_text(
        "🔍 Fetching latest news from all RSS feeds... This may take a moment.",
        reply_markup=bot.get_main_keyboard()
    )
    
    try:
        # Fetch news immediately
        scraper = NewsScraper()
        news_items = scraper.scrape_news(
            keywords=config.KEYWORDS,
            rss_feeds=rss_feeds,
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
    bot = TelegramNewsBot()
    user_id = str(update.effective_user.id)

    # --- Main menu commands ---
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

    elif text == "➕ Add":
        await add_menu(update, context)

    elif text == "➕ Add Asset":
        await update.message.reply_text("💼 Send me the asset symbol (e.g., BTC or BTC/USDT).")
        context.user_data["state"] = WAITING_FOR_ASSET

    elif text == "➕ Add News Source":
        await update.message.reply_text("🌐 Send me the news source URL (e.g., https://cointelegraph.com/rss).")
        context.user_data["state"] = WAITING_FOR_SOURCE

    elif text == "📋 My Assets":
        with DatabaseService() as db:
            assets = db.get_user_assets(user_id)
        if assets:
            msg = "📋 *Your Assets:*\n\n" + "\n".join(f"• {a}" for a in assets)
            context.user_data["state"] = WAITING_FOR_REMOVE_ASSET
        else:
            msg = "You don’t have any saved assets."
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "📋 My Sources":
        with DatabaseService() as db:
            sources = db.get_user_news_sources(user_id)
        if sources:
            msg = "📋 *Your News Sources:*\n\n" + "\n".join(f"• {s}" for s in sources)
            context.user_data["state"] = WAITING_FOR_REMOVE_SOURCE
        else:
            msg = "You don’t have any saved news sources."
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "❌ Remove":
        await update.message.reply_text("Choose what you want to remove:", reply_markup=bot.get_remove_keyboard())

    elif text == "⬅️ Back":
        context.user_data["state"] = None
        await update.message.reply_text("Back to main menu:", reply_markup=bot.get_main_keyboard())

    # --- Stateful inputs (adding/removing) ---
    elif context.user_data.get("state") == WAITING_FOR_ASSET:
        symbol = text.strip().upper()
        if "/" not in symbol:
            symbol = f"{symbol}/USDT"
        with DatabaseService() as db:
            db.add_user_asset(user_id, symbol)
        await update.message.reply_text(f"✅ Asset *{symbol}* added to your watchlist.", parse_mode="Markdown")
        context.user_data["state"] = None

    elif context.user_data.get("state") == WAITING_FOR_SOURCE:
        raw_url = text.strip()
        url = normalize_rss_url(raw_url)
        with DatabaseService() as db:
            success = db.add_news_source(user_id, url)
        if success:
            await update.message.reply_text(f"✅ News source added:\n{url}", parse_mode="Markdown", reply_markup=bot.get_main_keyboard())
        else:
            await update.message.reply_text(f"❌ Failed to add news source:\n{raw_url}", parse_mode="Markdown", reply_markup=bot.get_main_keyboard())
        context.user_data["state"] = None

    elif context.user_data.get("state") == WAITING_FOR_REMOVE_ASSET:
        # Ignore menu button clicks
        if text in ["❌ Remove Asset", "❌ Remove News Source", "❌ Remove", "⬅️ Back"]:
            return

        symbol = text.strip().upper()
        if "/" not in symbol:
            symbol = f"{symbol}/USDT"

        with DatabaseService() as db:
            success = db.remove_user_asset(user_id, symbol)

        if success:
            await update.message.reply_text(f"🗑️ Asset *{symbol}* removed from your watchlist.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Could not remove asset *{symbol}*.", parse_mode="Markdown")

        context.user_data["state"] = None


    elif context.user_data.get("state") == WAITING_FOR_REMOVE_SOURCE:
        # Ignore menu button clicks
        if text in ["❌ Remove Asset", "❌ Remove News Source", "❌ Remove", "⬅️ Back"]:
            return

        raw_url = text.strip()
        url = normalize_rss_url(raw_url)

        with DatabaseService() as db:
            success = db.remove_news_source(user_id, url)

        if success:
            await update.message.reply_text(f"🗑️ News source removed:\n{url}")
        else:
            await update.message.reply_text(f"❌ Could not remove news source:\n{raw_url}")

        context.user_data["state"] = None


    elif text == "❌ Remove Asset":
        with DatabaseService() as db:
            assets = db.get_user_assets(user_id)
        if assets:
            msg = "📋 *Your Assets:*\n" + "\n".join(f"• {a}" for a in assets)
            msg += "\n\n❌ Send me the asset symbol to remove (e.g., BTC/USDT)."
            context.user_data["state"] = WAITING_FOR_REMOVE_ASSET
        else:
            msg = "You don’t have any saved assets."
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "❌ Remove News Source":
        with DatabaseService() as db:
            sources = db.get_user_news_sources(user_id)
        if sources:
            msg = "📋 *Your News Sources:*\n" + "\n".join(f"• {s}" for s in sources)
            msg += "\n\n❌ Send me the URL to remove."
            context.user_data["state"] = WAITING_FOR_REMOVE_SOURCE
        else:
            msg = "You don’t have any saved news sources."
        await update.message.reply_text(msg, parse_mode="Markdown")


    # --- Unknown command ---
    else:
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

async def add_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = TelegramNewsBot()
    message = "➕ *Add Menu*\n\nChoose what you want to add:"
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=bot.get_add_keyboard()
    )



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

