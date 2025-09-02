import config
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    message = f"🤖 *News Bot Started!*\n\n"
    message += f"📅 Scheduled time: {config.SCHEDULE_TIME}\n"
    message += f"🔍 Keywords: {', '.join(config.KEYWORDS)}\n"
    message += f"🌐 Websites: {len(config.WEBSITES)} sources\n\n"
    message += "I'll send you news updates automatically every day!"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    message = f"📊 *Bot Status*\n\n"
    message += f"⏰ Schedule: {config.SCHEDULE_TIME} daily\n"
    message += f"🏷️ Keywords: {', '.join(config.KEYWORDS)}\n"
    message += f"📰 Max news per keyword: {config.MAX_NEWS_PER_KEYWORD}\n"
    message += f"🕒 Cache duration: {config.NEWS_CACHE_HOURS} hours\n"
    message += f"✅ Status: Running"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    message = f"🆘 *News Bot Help*\n\n"
    message += f"/start - Start the bot\n"
    message += f"/status - Check bot status\n"
    message += f"/help - Show this help\n\n"
    message += f"The bot automatically sends news at {config.SCHEDULE_TIME} daily based on your keywords."
    
    await update.message.reply_text(message, parse_mode='Markdown')

# Handler list for easy import
handlers = [
    CommandHandler('start', start),
    CommandHandler('status', status),
    CommandHandler('help', help_command),
]