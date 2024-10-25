import time
import requests
import datetime
import os
import signal
import logging

# Telegram bot details
bot_token = 'BOT_TOKEN'
# List of chat IDs to receive notifications
chat_ids = ['CHAT_ID', 'CHAT_ID']  # Add the secondary user's chat ID here

# Water intake goal and tracking
daily_goal_liters = 2.5  # Set your daily goal here
current_intake = 0
last_update_time = None

# To handle graceful shutdown
shutdown_flag = False

# Set up logging
log_file = 'water_reminder.log'
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_message(message, level='info'):
    """
    Log a message to the file and print to console.
    Levels: 'info', 'warning', 'error'
    """
    print(f"{datetime.datetime.now()} - {message}")
    if level == 'info':
        logging.info(message)
    elif level == 'warning':
        logging.warning(message)
    elif level == 'error':
        logging.error(message)

def signal_handler(signum, frame):
    global shutdown_flag
    shutdown_flag = True
    log_message("Shutdown signal received", 'warning')

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def send_telegram_message(message, specific_chat_id=None):
    """
    Send message to either a specific chat ID or all chat IDs
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    recipients = [specific_chat_id] if specific_chat_id else chat_ids
    
    responses = []
    for chat_id in recipients:
        params = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            log_message(f"Sent message to {chat_id}: {message}")
            responses.append(response.json())
        except requests.RequestException as e:
            log_message(f"Error sending message to {chat_id}: {e}", 'error')
    
    return responses

def get_telegram_updates(offset):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log_message(f"Error getting updates: {e}", 'error')
        return {"ok": False, "result": []}

def process_user_input(text, from_chat_id):
    global current_intake, last_update_time
    if text.lower() == "/clear":
        return clear_chat(from_chat_id)
    elif text.lower() == "/reset":
        return reset_daily_intake()
    elif text.lower() == "/start":
        return "Welcome to the Water Reminder bot! You'll receive notifications about water intake. Use numbers to log water intake in liters, /clear to clear chat, or /reset to reset daily intake."
    
    try:
        amount = float(text)
        if amount < 0:
            return "Please enter a positive number for your water intake."
        current_intake += amount
        last_update_time = datetime.datetime.now()
        remaining = max(0, daily_goal_liters - current_intake)
        log_message(f"Processed input: {amount}L. Total: {current_intake:.1f}L. Remaining: {remaining:.1f}L")
        # Notify all users about the update
        update_message = f"Update: {amount}L added. Total intake: {current_intake:.1f}L. Remaining: {remaining:.1f}L"
        for chat_id in chat_ids:
            if chat_id != from_chat_id:
                send_telegram_message(update_message, chat_id)
        return f"Added {amount}L. Total intake: {current_intake:.1f}L. Remaining: {remaining:.1f}L"
    except ValueError:
        log_message(f"Invalid input received: {text}", 'warning')
        return "Please enter a valid number for your water intake in liters, or use /clear to clear chat or /reset to reset daily intake."

def check_daily_reset():
    global current_intake, last_update_time
    now = datetime.datetime.now()
    if last_update_time and now.date() > last_update_time.date():
        current_intake = 0
        last_update_time = now
        log_message("Daily reset performed")
        return True
    return False

def clear_chat(from_chat_id):
    log_message("Chat cleared")
    send_telegram_message("Chat cleared. Previous messages are still visible to you, but I've reset my memory of our conversation.", from_chat_id)
    return "Chat cleared. What would you like to do next?"

def reset_daily_intake():
    global current_intake, last_update_time
    current_intake = 0
    last_update_time = datetime.datetime.now()
    log_message("Daily intake reset")
    # Notify all users about the reset
    message = f"Daily intake has been reset to 0L. Your goal is still {daily_goal_liters}L."
    send_telegram_message(message)
    return message

def water_reminder():
    global current_intake, last_update_time, shutdown_flag
    update_offset = 0
    last_reminder_time = datetime.datetime.now()
    last_processed_update_id = 0

    log_message("Water reminder started")

    while not shutdown_flag:
        try:
            if check_daily_reset():
                send_telegram_message("New day started! Your water intake has been reset to 0L.")

            now = datetime.datetime.now()
            if (now - last_reminder_time).total_seconds() >= 3600:  # 1 hour
                remaining = max(0, daily_goal_liters - current_intake)
                message = f"Reminder: You still need to drink {remaining:.1f}L of water today. How much have you had since last update?"
                send_telegram_message(message)
                last_reminder_time = now
                log_message("Sent hourly reminder")

            updates = get_telegram_updates(update_offset)
            for update in updates.get("result", []):
                update_id = update["update_id"]
                if update_id > last_processed_update_id:
                    message = update.get("message", {})
                    if "text" in message:
                        from_chat_id = str(message["chat"]["id"])
                        log_message(f"Received message from {from_chat_id}: {message['text']}")
                        response = process_user_input(message["text"], from_chat_id)
                        send_telegram_message(response, from_chat_id)
                    last_processed_update_id = update_id
                update_offset = update_id + 1

            time.sleep(10)  # Check for updates every 10 seconds
        except Exception as e:
            log_message(f"Error in main loop: {e}", 'error')
            time.sleep(60)  # Wait a minute before retrying if there's an error

    log_message("Water reminder shutting down")
    send_telegram_message("Water reminder app is shutting down. Goodbye!")

if __name__ == "__main__":
    log_message("Application started")
    send_telegram_message("Water reminder app started. What's your current water intake in liters? Use /clear to clear chat or /reset to reset daily intake.")
    water_reminder()