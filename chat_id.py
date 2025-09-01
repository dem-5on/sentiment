from telegram.ext import Application, MessageHandler, filters
import config

async def get_chat_id(update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    message = f"Chat ID: {chat_id}\nUser ID: {user_id}\nUsername: @{username}"
    print(message)
    await update.message.reply_text(message)

def main():
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, get_chat_id))
    
    print("Send any message to your bot to get the Chat ID...")
    app.run_polling()

if __name__ == "__main__":
    main()