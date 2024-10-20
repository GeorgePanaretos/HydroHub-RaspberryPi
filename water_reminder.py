import time
import requests
import datetime
import os

# Telegram bot details
bot_token = 'TOKEN'
chat_id = 'CHAT_ID'

# Water intake goal and tracking
daily_goal_liters = 2.5  # Set your daily goal here
current_intake = 0
last_update_time = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.get(url, params=params)
    return response.json()

def get_telegram_updates(offset):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"offset": offset, "timeout": 30}
    response = requests.get(url, params=params)
    return response.json()

def process_user_input(text):
    global current_intake, last_update_time
    try:
        amount = float(text)
        current_intake += amount
        last_update_time = datetime.datetime.now()
        remaining = max(0, daily_goal_liters - current_intake)
        return f"Added {amount}L. Total intake: {current_intake}L. Remaining: {remaining:.1f}L"
    except ValueError:
        return "Please enter a valid number for your water intake in liters."

def check_daily_reset():
    global current_intake, last_update_time
    now = datetime.datetime.now()
    if last_update_time and now.date() > last_update_time.date():
        current_intake = 0
        last_update_time = now
        return True
    return False

def water_reminder():
    global current_intake, last_update_time
    update_offset = 0
    last_reminder_time = datetime.datetime.now()

    while True:
        if check_daily_reset():
            send_telegram_message("New day started! Your water intake has been reset to 0L.")

        now = datetime.datetime.now()
        if (now - last_reminder_time).total_seconds() >= 3600:  # 1 hour
            remaining = max(0, daily_goal_liters - current_intake)
            message = f"Reminder: You still need to drink {remaining:.1f}L of water today. How much have you had since last update?"
            send_telegram_message(message)
            last_reminder_time = now

        updates = get_telegram_updates(update_offset)
        for update in updates.get("result", []):
            update_offset = update["update_id"] + 1
            message = update.get("message", {})
            if "text" in message:
                response = process_user_input(message["text"])
                send_telegram_message(response)

        time.sleep(60)  # Check for updates every minute

if __name__ == "__main__":
    send_telegram_message("Water reminder app started. What's your current water intake in liters?")
    water_reminder()
