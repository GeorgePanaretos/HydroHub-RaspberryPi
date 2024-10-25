# HydroHub-RaspberryPi


1. Set up your Raspberry Pi:
   a. If you haven't already, install Raspberry Pi OS on your SD card.
   b. Connect your Raspberry Pi to power, monitor, keyboard, and mouse.
   c. Boot up the Raspberry Pi and connect it to the internet.

2. Prepare the Raspberry Pi:
   a. Open a terminal window.
   b. Update your system:
      ```
      sudo apt update
      sudo apt upgrade
      ```
   c. Install Python and pip if they're not already installed:
      ```
      sudo apt install python3 python3-pip
      ```
   d. Install the required library:
      ```
      pip3 install requests
      ```

3. Create a Telegram bot:
   a. Open the Telegram app on your phone.
   b. Search for "BotFather" and start a chat.
   c. Send the command `/newbot` to create a new bot.
   d. Follow the prompts to name your bot and choose a username for it.
   e. BotFather will give you a token. Save this token; you'll need it later.

4. Get your Telegram chat ID:
   a. Start a chat with your new bot in Telegram.
   b. Send any message to the bot.
   c. Open a web browser and go to:
      ```
      https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
      ```
      Replace <YOUR_BOT_TOKEN> with the token you received from BotFather.
   d. Look for the "chat" object in the response and find your "id". This is your chat ID.

5. Create the water reminder script:
   a. On your Raspberry Pi, open a text editor (like Nano):
      ```
      nano water_reminder.py
      ```
   b. Copy and paste the following code:

```python
# Telegram bot details
bot_token = 'YOUR_BOT_TOKEN'
chat_id = 'YOUR_CHAT_ID'

```

   c. Replace 'YOUR_BOT_TOKEN' and 'YOUR_CHAT_ID' with your actual bot token and chat ID.
   d. Save the file and exit the editor (in Nano, press Ctrl+X, then Y, then Enter).

6. Test the app:
   a. Run the script:
      ```
      python3 water_reminder.py
      ```
   b. You should receive a message on Telegram immediately, and then every hour after that.
   c. To stop the script, press Ctrl+C in the terminal.

7. Run the app in the background (optional):
   If you want the app to keep running even when you close the terminal:
   a. Use the `nohup` command to run the script:
      ```
      nohup python3 water_reminder.py &
      ```
   b. The app will now run in the background. You can close the terminal if you wish.
   c. To stop the app later, you'll need to find its process ID and kill it:
      ```
      ps aux | grep water_reminder.py
      kill <PROCESS_ID>
      ```
      Replace <PROCESS_ID> with the ID you find from the `ps` command.

8. Set up autostart (optional):
   To make the app start automatically when your Raspberry Pi boots:
   a. Open the RC local file:
      ```
      sudo nano /etc/rc.local
      ```
   b. Before the `exit 0` line, add:
      ```
      python3 /home/pi/water_reminder.py &
      ```
      (Adjust the path if your script is located elsewhere)
   c. Save and exit (Ctrl+X, Y, Enter).
   d. Reboot your Raspberry Pi to test:
      ```
      sudo reboot
      ```
