import time
import requests
import datetime
import os
import signal
import logging
import sqlite3
from dataclasses import dataclass
from typing import Optional

# Telegram bot details
bot_token = 'BOT_TOKEN'
# List of chat IDs to receive notifications
chat_ids = ['CHAT_ID', 'CHAT_ID']  # Add the secondary user's chat ID here

# Configuration
QUIET_HOURS_START = datetime.time(0, 0)  # 12:00 AM
QUIET_HOURS_END = datetime.time(7, 30)    # 7:30 AM
DEFAULT_DAILY_GOAL = 2.5  # Default daily goal in liters

# Set up logging
logging.basicConfig(
    filename='water_reminder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class UserSession:
    chat_id: str
    current_intake: float
    daily_goal: float
    last_update_time: datetime.datetime
    goal_reached_notified: bool

class WaterReminderDB:
    def __init__(self, db_name='water_reminder.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    chat_id TEXT PRIMARY KEY,
                    current_intake REAL,
                    daily_goal REAL,
                    last_update_time TEXT,
                    goal_reached_notified INTEGER
                )
            ''')
            conn.commit()

    def get_user_session(self, chat_id: str) -> UserSession:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM user_sessions WHERE chat_id = ?',
                (chat_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                # Create new session if doesn't exist
                session = UserSession(
                    chat_id=chat_id,
                    current_intake=0.0,
                    daily_goal=DEFAULT_DAILY_GOAL,
                    last_update_time=datetime.datetime.now(),
                    goal_reached_notified=False
                )
                self.save_user_session(session)
                return session
            
            return UserSession(
                chat_id=row[0],
                current_intake=row[1],
                daily_goal=row[2],
                last_update_time=datetime.datetime.fromisoformat(row[3]),
                goal_reached_notified=bool(row[4])
            )

    def save_user_session(self, session: UserSession):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_sessions 
                (chat_id, current_intake, daily_goal, last_update_time, goal_reached_notified)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session.chat_id,
                session.current_intake,
                session.daily_goal,
                session.last_update_time.isoformat(),
                int(session.goal_reached_notified)
            ))
            conn.commit()

    def reset_user_session(self, chat_id: str):
        session = self.get_user_session(chat_id)
        session.current_intake = 0
        session.goal_reached_notified = False
        session.last_update_time = datetime.datetime.now()
        self.save_user_session(session)
        return session

class WaterReminder:
    def __init__(self, bot_token: str, chat_ids: list[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.db = WaterReminderDB()
        self.shutdown_flag = False

    def log_message(self, message: str, level: str = 'info'):
        print(f"{datetime.datetime.now()} - {message}")
        if level == 'info':
            logging.info(message)
        elif level == 'warning':
            logging.warning(message)
        elif level == 'error':
            logging.error(message)

    def is_quiet_hours(self) -> bool:
        current_time = datetime.datetime.now().time()
        if QUIET_HOURS_START <= QUIET_HOURS_END:
            return QUIET_HOURS_START <= current_time <= QUIET_HOURS_END
        return current_time >= QUIET_HOURS_START or current_time <= QUIET_HOURS_END

    def should_send_reminder(self, session: UserSession) -> bool:
        if session.current_intake >= session.daily_goal:
            return False
        return not self.is_quiet_hours()

    def send_telegram_message(self, message: str, specific_chat_id: Optional[str] = None, 
                            respect_quiet_hours: bool = True) -> list:
        if respect_quiet_hours and self.is_quiet_hours():
            self.log_message("Message delayed due to quiet hours: " + message)
            return []

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        recipients = [specific_chat_id] if specific_chat_id else self.chat_ids
        
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
                self.log_message(f"Sent message to {chat_id}: {message}")
                responses.append(response.json())
            except requests.RequestException as e:
                self.log_message(f"Error sending message to {chat_id}: {e}", 'error')
        
        return responses

    def check_and_notify_goal_reached(self, session: UserSession) -> bool:
        if session.current_intake >= session.daily_goal and not session.goal_reached_notified:
            congratulations_message = (
                f"🎉 Congratulations! You've reached your daily water intake goal of {session.daily_goal}L!\n"
                f"Current intake: {session.current_intake:.1f}L\n"
                "You won't receive more reminders today, but you can continue tracking additional intake."
            )
            self.send_telegram_message(congratulations_message, session.chat_id, respect_quiet_hours=False)
            session.goal_reached_notified = True
            self.db.save_user_session(session)
            return True
        return False

    def process_user_input(self, text: str, from_chat_id: str) -> str:
        session = self.db.get_user_session(from_chat_id)
        
        if text.lower() == "/clear":
            return self.clear_chat(from_chat_id)
        elif text.lower() == "/reset":
            return self.reset_daily_intake(from_chat_id)
        elif text.lower() == "/start":
            return ("Welcome to the Water Reminder bot! You'll receive notifications about water intake "
                    f"(except during quiet hours: {QUIET_HOURS_START.strftime('%I:%M %p')} - "
                    f"{QUIET_HOURS_END.strftime('%I:%M %p')} and after reaching your daily goal). "
                    "Use numbers to log water intake in liters, /clear to clear chat, "
                    "or /reset to reset daily intake.")
        elif text.lower() == "/status":
            return self.get_status(from_chat_id)
        
        try:
            amount = float(text)
            if amount < 0:
                return "Please enter a positive number for your water intake."
            
            session.current_intake += amount
            session.last_update_time = datetime.datetime.now()
            remaining = max(0, session.daily_goal - session.current_intake)
            
            self.log_message(
                f"User {from_chat_id} processed input: {amount}L. "
                f"Total: {session.current_intake:.1f}L. Remaining: {remaining:.1f}L"
            )
            
            # Save updated session
            self.db.save_user_session(session)
            
            # Prepare the update message
            update_message = f"Update: {amount}L added. Total intake: {session.current_intake:.1f}L"
            if remaining > 0:
                update_message += f". Remaining: {remaining:.1f}L"
            else:
                update_message += f". Exceeded goal by: {-remaining:.1f}L"
            
            # Notify other users about the update
            for chat_id in self.chat_ids:
                if chat_id != from_chat_id:
                    self.send_telegram_message(update_message, chat_id, respect_quiet_hours=False)
            
            # Check if goal has been reached
            self.check_and_notify_goal_reached(session)
            
            return update_message
            
        except ValueError:
            self.log_message(f"Invalid input received: {text}", 'warning')
            return ("Please enter a valid number for your water intake in liters, or use:\n"
                    "/clear - clear chat\n"
                    "/reset - reset daily intake\n"
                    "/status - check current status")

    def get_status(self, chat_id: str) -> str:
        session = self.db.get_user_session(chat_id)
        remaining = max(0, session.daily_goal - session.current_intake)
        if session.current_intake >= session.daily_goal:
            return (f"🎉 Goal reached! Current intake: {session.current_intake:.1f}L\n"
                    f"Exceeded goal by: {-remaining:.1f}L")
        else:
            return (f"Current intake: {session.current_intake:.1f}L\n"
                    f"Remaining to goal: {remaining:.1f}L")

    def check_daily_reset(self, chat_id: str) -> bool:
        session = self.db.get_user_session(chat_id)
        now = datetime.datetime.now()
        if now.date() > session.last_update_time.date():
            session = self.db.reset_user_session(chat_id)
            self.log_message(f"Daily reset performed for user {chat_id}")
            return True
        return False

    def clear_chat(self, chat_id: str) -> str:
        self.log_message(f"Chat cleared for user {chat_id}")
        self.send_telegram_message(
            "Chat cleared. Previous messages are still visible to you, but I've reset my memory of our conversation.",
            chat_id,
            respect_quiet_hours=False
        )
        return "Chat cleared. What would you like to do next?"

    def reset_daily_intake(self, chat_id: str) -> str:
        session = self.db.reset_user_session(chat_id)
        self.log_message(f"Daily intake reset for user {chat_id}")
        message = f"Daily intake has been reset to 0L. Your goal is still {session.daily_goal}L."
        self.send_telegram_message(message, chat_id, respect_quiet_hours=False)
        return message

    def run(self):
        update_offset = 0
        last_reminder_times = {chat_id: datetime.datetime.now() for chat_id in self.chat_ids}
        last_processed_update_id = 0

        self.log_message("Water reminder started")
        self.send_telegram_message(
            "Water reminder app started. What's your current water intake in liters? "
            "Use /clear to clear chat or /reset to reset daily intake.",
            respect_quiet_hours=False
        )

        while not self.shutdown_flag:
            try:
                # Check daily reset for all users
                for chat_id in self.chat_ids:
                    if self.check_daily_reset(chat_id):
                        self.send_telegram_message(
                            "New day started! Your water intake has been reset to 0L.",
                            chat_id,
                            respect_quiet_hours=False
                        )

                # Send reminders if needed
                now = datetime.datetime.now()
                for chat_id in self.chat_ids:
                    session = self.db.get_user_session(chat_id)
                    if ((now - last_reminder_times[chat_id]).total_seconds() >= 3600 and 
                            self.should_send_reminder(session)):
                        remaining = max(0, session.daily_goal - session.current_intake)
                        message = (f"Reminder: You still need to drink {remaining:.1f}L of water today. "
                                 "How much have you had since last update?")
                        self.send_telegram_message(message, chat_id)
                        last_reminder_times[chat_id] = now
                        self.log_message(f"Sent hourly reminder to user {chat_id}")

                # Process updates
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {"offset": update_offset, "timeout": 30}
                try:
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    updates = response.json()
                    
                    for update in updates.get("result", []):
                        update_id = update["update_id"]
                        if update_id > last_processed_update_id:
                            message = update.get("message", {})
                            if "text" in message:
                                from_chat_id = str(message["chat"]["id"])
                                self.log_message(f"Received message from {from_chat_id}: {message['text']}")
                                response = self.process_user_input(message["text"], from_chat_id)
                                self.send_telegram_message(response, from_chat_id, respect_quiet_hours=False)
                            last_processed_update_id = update_id
                        update_offset = update_id + 1

                except requests.RequestException as e:
                    self.log_message(f"Error getting updates: {e}", 'error')

                time.sleep(10)  # Check for updates every 10 seconds
                
            except Exception as e:
                self.log_message(f"Error in main loop: {e}", 'error')
                time.sleep(60)  # Wait a minute before retrying if there's an error

        self.log_message("Water reminder shutting down")
        self.send_telegram_message("Water reminder app is shutting down. Goodbye!", respect_quiet_hours=False)

def main():
    reminder = WaterReminder(bot_token, chat_ids)
    
    def signal_handler(signum, frame):
        reminder.shutdown_flag = True
        reminder.log_message("Shutdown signal received", 'warning')

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    reminder.run()

if __name__ == "__main__":
    main()