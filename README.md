# HydroHub-RaspberryPi

A Raspberry Pi-powered Telegram bot that helps you track your daily water intake and sends timely reminders to stay hydrated. This system combines hardware reliability with user-friendly interaction through Telegram.

## 🌟 Features

- 🚰 Track daily water intake
- ⏰ Hourly reminders during active hours
- 🎯 Daily water intake goal tracking
- 🌙 Quiet hours support
- 👥 Multi-user support(sharing one common session)
- 📊 Status updates and progress tracking
- 🔄 Automatic daily reset
- 🤖 Runs on Raspberry Pi
- 🔧 Auto-start capability
- 📝 Comprehensive logging

## 📋 Requirements

### Hardware
- Raspberry Pi (any model with network connectivity)
- SD card (8GB+ recommended)
- Power supply for Raspberry Pi
- Internet connection

### Software
- Raspberry Pi OS
- Python 3.6+
- `requests` library
- Telegram account
- Telegram Bot Token

## 🛠️ Installation

### 1. Raspberry Pi Setup

1. Install Raspberry Pi OS:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python and pip if not present
   sudo apt install python3 python3-pip
   ```

2. Install Required Library:
   ```bash
   pip3 install requests
   ```

### 2. Telegram Bot Setup

1. Create a new bot:
   - Open Telegram and search for "BotFather"
   - Send `/newbot` command
   - Follow prompts to name your bot
   - Save the bot token provided

2. Get Your Chat ID:
   - Start a chat with your new bot
   - Send any message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

### 3. Software Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/hydrohub.git
   cd hydrohub
   ```

2. Configure the bot:
   ```bash
   nano water_reminder.py
   ```
   
3. Update these variables:
   ```python
   bot_token = 'YOUR_BOT_TOKEN'
   chat_ids = ['YOUR_CHAT_ID', 'ADDITIONAL_CHAT_ID']  # Add multiple IDs if needed
   daily_goal_liters = 2.5  # Adjust as needed
   ```

## ⚙️ Configuration

### Quiet Hours
```python
QUIET_HOURS_START = datetime.time(0, 0)    # 12:00 AM
QUIET_HOURS_END = datetime.time(7, 30)     # 7:30 AM
```

### Daily Goal
```python
daily_goal_liters = 2.5  # Set your daily goal in liters
```

## 🚀 Running the System

### Manual Start
```bash
python3 water_reminder.py
```

### Background Operation
```bash
nohup python3 water_reminder.py &
```

### Auto-start Setup
1. Edit RC local file:
   ```bash
   sudo nano /etc/rc.local
   ```

2. Add before `exit 0`:
   ```bash
   python3 /home/pi/hydrohub/water_reminder.py &
   ```

3. Reboot to test:
   ```bash
   sudo reboot
   ```

## 📱 Usage

### Bot Commands
- Send number (e.g., `0.5`) - Log water intake in liters
- `/start` - Get welcome message and instructions
- `/status` - Check current water intake status
- `/reset` - Reset daily intake to 0
- `/clear` - Clear chat history

### Features in Detail

#### 1. Automatic Daily Reset
- Midnight reset
- All users notified
- Progress tracking restarts

#### 2. Goal Tracking
- Real-time progress updates
- Goal completion notifications
- Smart reminder system

#### 3. Multi-User Support
- Synchronized updates
- Shared tracking
- Individual interaction

#### 4. Logging System
- File: `water_reminder.log`
- Detailed timestamps
- Error tracking
- Performance monitoring

## 🛡️ Security

- Store bot token securely
- Keep chat IDs private
- Use environment variables for sensitive data
- Regular system updates
- Monitor access logs

## 🔍 Troubleshooting

### Common Issues

1. Bot Not Responding
   ```bash
   # Check if process is running
   ps aux | grep water_reminder.py
   
   # Check logs
   tail -f water_reminder.log
   ```

2. Permission Issues
   ```bash
   # Fix permissions
   chmod +x water_reminder.py
   ```

3. Network Problems
   ```bash
   # Test network
   ping api.telegram.org
   ```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Telegram Bot API
- Raspberry Pi Foundation
- Python `requests` library contributors
- Community feedback and contributions
