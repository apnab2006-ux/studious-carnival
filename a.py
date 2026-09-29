import os
import time
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Load keys from environment variables
MINIMAX_API_KEY = os.environ.get("sk-cp-jqkYZKrokpSo6XdjlPb7cHA2kZfLdhdZwgtX15DsiwBAbFjb221rKvZtuZvPk0xEy7AaEZnD94ugiuDisZ8U1sLs5qfzCAHog6ti5fjjUsqZprpRqiNzdBg")
TELEGRAM_BOT_TOKEN = os.environ.get("8925295068:AAGOj3L0OMAABkyCiRwX2gfgPYoYRM11_zA")

if not MINIMAX_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise ValueError("Error: Both MINIMAX_API_KEY and TELEGRAM_BOT_TOKEN must be set as environment variables.")

# Base headers for MiniMax V2 endpoint
MINIMAX_HEADERS = {
    "Authorization": f"Bearer {MINIMAX_API_KEY}",
    "Content-Type": "application/json"
}

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send me a descriptive text prompt, and I will generate a 5-second cinematic AI video for you using MiniMax H3."
    )

# Direct polling loop wrapped in an async function to keep Telegram responsive
async def request_and_poll_video(prompt_text):
    create_url = "https://minimax.io"
    payload = {
        "model": "MiniMax-H3",
        "content": [{"type": "text", "text": prompt_text}],
        "duration": 5,
        "ratio": "16:9"
    }
    
    # Submit task
    response = requests.post(create_url, headers=MINIMAX_HEADERS, json=payload)
    if response.status_code != 200:
        return None, f"MiniMax Error (Status {response.status_code}): {response.text}"
        
    task_data = response.json()
    task_id = task_data.get("task_id")
    if not task_id:
        return None, "Failed to retrieve a task ID from MiniMax."
        
    # Poll status loop
    query_url = f"https://minimax.io{task_id}"
    while True:
        # Use asyncio.sleep so the server thread isn't blocked completely
        await asyncio.sleep(10)
        status_response = requests.get(query_url, headers=MINIMAX_HEADERS).json()
        status = status_response.get("status")
        
        if status == "Success":
            return status_response.get("file_id"), None
        elif status == "Fail":
            return None, "MiniMax engine failed to compile the video."

# Message handler that triggers when a user sends a text prompt
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_prompt = update.message.text
    status_message = await update.message.reply_text("🚀 Submitting your prompt to MiniMax H3... Please wait.")
    
    try:
        # Run the polling loop
        video_url, error = await request_and_poll_video(user_prompt)
        
        if error:
            await status_message.edit_text(f"❌ Generation failed: {error}")
            return
            
        await status_message.edit_text("⏳ Video ready! Uploading it to Telegram...")
        
        # Send the file link back to the user
        # Note: You can also use context.bot.send_video(chat_id, video=video_url) if Telegram can fetch the URL directly
        await update.message.reply_text(f"🎉 Here is your generated video link:\n{video_url}")
        
    except Exception as e:
        await status_message.edit_text(f"❌ An unexpected error occurred: {str(e)}")

def main():
    # Initialize the Telegram Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))
    
    # Start polling Telegram updates
    print("🤖 Telegram Bot is running... Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
