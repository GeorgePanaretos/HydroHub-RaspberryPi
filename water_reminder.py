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
goal_reached_notified = False  # Track if we've notified about reaching the goal

# Quiet hours configuration
QUIET_HOURS_START = datetime.time(0, 0)  # 12:00 AM
QUIET_HOURS_END = datetime.time(7, 30)    # 7:30 AM

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

def is_quiet_hours():
    """
    Check if current time is within quiet hours
    """
    current_time = datetime.datetime.now().time()
    
    if QUIET_HOURS_START <= QUIET_HOURS_END:
        return QUIET_HOURS_START <= current_time <= QUIET_HOURS_END
    else:  # Handle case when quiet hours span across midnight
        return current_time >= QUIET_HOURS_START or current_time <= QUIET_HOURS_END

def should_send_reminder():
    """
    Check if we should send a reminder based on goal completion and quiet hours
    """
    if current_intake >= daily_goal_liters:
        return False
    return not is_quiet_hours()

def signal_handler(signum, frame):
    global shutdown_flag
    shutdown_flag = True
    log_message("Shutdown signal received", 'warning')

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def send_telegram_message(message, specific_chat_id=None, respect_quiet_hours=True):
    """
    Send message to either a specific chat ID or all chat IDs
    respect_quiet_hours: if True, won't send non-essential messages during quiet hours
    """
    # Don't send notifications during quiet hours unless it's marked as essential
    if respect_quiet_hours and is_quiet_hours():
        log_message("Message delayed due to quiet hours: " + message)
        return []

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

def check_and_notify_goal_reached():
    """
    Check if goal has been reached and send notification if it's the first time
    """
    global goal_reached_notified
    if current_intake >= daily_goal_liters and not goal_reached_notified:
        congratulations_message = (
            f"🎉 Congratulations! You've reached your daily water intake goal of {daily_goal_liters}L!\n"
            f"Current intake: {current_intake:.1f}L\n"
            "You won't receive more reminders today, but you can continue tracking additional intake."
        )
        send_telegram_message(congratulations_message, respect_quiet_hours=False)
        goal_reached_notified = True
        return True
    return False

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
        return ("Welcome to the Water Reminder bot! You'll receive notifications about water intake "
                "(except during quiet hours: 12:00 AM - 7:30 AM and after reaching your daily goal). "
                "Use numbers to log water intake in liters, /clear to clear chat, or /reset to reset daily intake.")
    elif text.lower() == "/status":
        return get_status()
    
    try:
        amount = float(text)
        if amount < 0:
            return "Please enter a positive number for your water intake."
        current_intake += amount
        last_update_time = datetime.datetime.now()
        remaining = max(0, daily_goal_liters - current_intake)
        log_message(f"Processed input: {amount}L. Total: {current_intake:.1f}L. Remaining: {remaining:.1f}L")
        
        # Prepare the update message
        update_message = f"Update: {amount}L added. Total intake: {current_intake:.1f}L"
        if remaining > 0:
            update_message += f". Remaining: {remaining:.1f}L"
        else:
            update_message += f". Exceeded goal by: {-remaining:.1f}L"
        
        # Notify all users about the update
																													 
        for chat_id in chat_ids:
            if chat_id != from_chat_id:
                send_telegram_message(update_message, chat_id, respect_quiet_hours=False)
        
        # Check if goal has been reached
        check_and_notify_goal_reached()
        
        return update_message
    except ValueError:
        log_message(f"Invalid input received: {text}", 'warning')
        return ("Please enter a valid number for your water intake in liters, or use:\n"
                "/clear - clear chat\n"
                "/reset - reset daily intake\n"
                "/status - check current status")

def get_status():
    """
    Get current status of water intake
    """
    remaining = max(0, daily_goal_liters - current_intake)
    if current_intake >= daily_goal_liters:
        return (f"🎉 Goal reached! Current intake: {current_intake:.1f}L\n"
                f"Exceeded goal by: {-remaining:.1f}L")
    else:
        return (f"Current intake: {current_intake:.1f}L\n"
                f"Remaining to goal: {remaining:.1f}L")

def check_daily_reset():
    global current_intake, last_update_time, goal_reached_notified
    now = datetime.datetime.now()
    if last_update_time and now.date() > last_update_time.date():
        current_intake = 0
        goal_reached_notified = False
        last_update_time = now
        log_message("Daily reset performed")
        return True
    return False

def clear_chat(from_chat_id):
    log_message("Chat cleared")
    send_telegram_message("Chat cleared. Previous messages are still visible to you, but I've reset my memory of our conversation.", 
                         from_chat_id, 
                         respect_quiet_hours=False)
    return "Chat cleared. What would you like to do next?"

def reset_daily_intake():
    global current_intake, last_update_time, goal_reached_notified
    current_intake = 0
    goal_reached_notified = False
    last_update_time = datetime.datetime.now()
    log_message("Daily intake reset")
									  
    message = f"Daily intake has been reset to 0L. Your goal is still {daily_goal_liters}L."
    send_telegram_message(message, respect_quiet_hours=False)
    return message

def water_reminder():
    global current_intake, last_update_time, shutdown_flag
    update_offset = 0
    last_reminder_time = datetime.datetime.now()
    last_processed_update_id = 0

    log_message("Water reminder started")
    send_telegram_message("Water reminder app started. What's your current water intake in liters? Use /clear to clear chat or /reset to reset daily intake.",
                         respect_quiet_hours=False)

    while not shutdown_flag:
        try:
            if check_daily_reset():
                send_telegram_message("New day started! Your water intake has been reset to 0L.", 
                                    respect_quiet_hours=False)

            now = datetime.datetime.now()
            # Only send reminder if we haven't reached the goal and it's not quiet hours
            if (now - last_reminder_time).total_seconds() >= 3600 and should_send_reminder():  # 1 hour
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
                        send_telegram_message(response, from_chat_id, respect_quiet_hours=False)
                    last_processed_update_id = update_id
                update_offset = update_id + 1

            time.sleep(10)  # Check for updates every 10 seconds
        except Exception as e:
            log_message(f"Error in main loop: {e}", 'error')
            time.sleep(60)  # Wait a minute before retrying if there's an error

    log_message("Water reminder shutting down")
    send_telegram_message("Water reminder app is shutting down. Goodbye!", respect_quiet_hours=False)

if __name__ == "__main__":
    log_message("Application started")
																																																				  
    water_reminder()