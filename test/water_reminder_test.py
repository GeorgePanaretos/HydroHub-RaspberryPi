import unittest
from unittest.mock import patch, MagicMock
import datetime
from water_reminder import (
    send_telegram_message,
    get_telegram_updates,
    process_user_input,
    check_daily_reset,
    clear_chat,
    reset_daily_intake,
    water_reminder
)

class TestWaterReminderApp(unittest.TestCase):

    def setUp(self):
        # Reset global variables before each test
        global current_intake, last_update_time, daily_goal_liters
        current_intake = 0
        last_update_time = None
        daily_goal_liters = 2.5

    @patch('water_reminder.requests.get')
    def test_send_telegram_message(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_get.return_value = mock_response

        result = send_telegram_message("Test message")
        self.assertEqual(result, {"ok": True})
        mock_get.assert_called_once()

    @patch('water_reminder.requests.get')
    def test_get_telegram_updates(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "result": []}
        mock_get.return_value = mock_response

        result = get_telegram_updates(0)
        self.assertEqual(result, {"ok": True, "result": []})
        mock_get.assert_called_once()

    def test_process_user_input_valid(self):
        result = process_user_input("0.5")
        self.assertIn("Added 0.5L", result)
        self.assertIn("Total intake: 0.5L", result)
        self.assertIn("Remaining: 2.0L", result)

    def test_process_user_input_invalid(self):
        result = process_user_input("not a number")
        self.assertIn("Please enter a valid number", result)

    def test_process_user_input_clear_command(self):
        with patch('water_reminder.clear_chat', return_value="Chat history cleared."):
            result = process_user_input("/clear")
            self.assertEqual(result, "Chat history cleared.")

    def test_process_user_input_reset_command(self):
        global current_intake
        current_intake = 1.5
        result = process_user_input("/reset")
        self.assertIn("Daily intake reset to 0L", result)
        self.assertEqual(current_intake, 0)

    def test_check_daily_reset_same_day(self):
        global last_update_time
        last_update_time = datetime.datetime.now()
        self.assertFalse(check_daily_reset())

    def test_check_daily_reset_next_day(self):
        global last_update_time, current_intake
        last_update_time = datetime.datetime.now() - datetime.timedelta(days=1)
        current_intake = 1.5
        self.assertTrue(check_daily_reset())
        self.assertEqual(current_intake, 0)

    @patch('water_reminder.requests.get')
    def test_clear_chat(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_get.return_value = mock_response

        result = clear_chat()
        self.assertEqual(result, "Chat history cleared.")
        self.assertEqual(mock_get.call_count, 1000)

    def test_reset_daily_intake(self):
        global current_intake, last_update_time
        current_intake = 1.5
        last_update_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        
        result = reset_daily_intake()
        self.assertIn("Daily intake reset to 0L", result)
        self.assertEqual(current_intake, 0)
        self.assertIsNotNone(last_update_time)
        self.assertGreater(last_update_time, datetime.datetime.now() - datetime.timedelta(seconds=1))

    @patch('water_reminder.send_telegram_message')
    @patch('water_reminder.get_telegram_updates')
    @patch('water_reminder.time.sleep', return_value=None)
    def test_water_reminder(self, mock_sleep, mock_get_updates, mock_send_message):
        mock_get_updates.return_value = {
            "ok": True,
            "result": [
                {"update_id": 1, "message": {"text": "0.5"}},
                {"update_id": 2, "message": {"text": "not a number"}},
                {"update_id": 3, "message": {"text": "/reset"}},
                {"update_id": 4, "message": {"text": "/clear"}}
            ]
        }
        
        # Run the water_reminder function for a short time
        def stop_loop():
            water_reminder.stop = True
        
        import threading
        timer = threading.Timer(0.1, stop_loop)
        timer.start()
        
        water_reminder()
        
        # Check that messages were sent and updates were processed
        self.assertTrue(mock_send_message.called)
        self.assertTrue(mock_get_updates.called)

if __name__ == '__main__':
    unittest.main()

```

These unit tests cover all the methods in our water reminder app. Here's a breakdown of what each test does:

1. `test_send_telegram_message`: Ensures that the function calls the Telegram API correctly.

2. `test_get_telegram_updates`: Verifies that the function retrieves updates from the Telegram API.

3. `test_process_user_input_valid`: Checks if the function correctly processes a valid water intake input.

4. `test_process_user_input_invalid`: Ensures the function handles invalid input appropriately.

5. `test_process_user_input_clear_command`: Verifies that the "/clear" command is processed correctly.

6. `test_process_user_input_reset_command`: Checks if the "/reset" command resets the daily intake.

7. `test_check_daily_reset_same_day`: Ensures the daily reset doesn't occur on the same day.

8. `test_check_daily_reset_next_day`: Verifies that the daily reset occurs correctly when a new day starts.

9. `test_clear_chat`: Checks if the clear_chat function attempts to delete messages.

10. `test_reset_daily_intake`: Ensures the reset_daily_intake function works correctly.

11. `test_water_reminder`: A more complex test that simulates the main loop of the app, checking if it sends messages and processes updates correctly.

To run these tests:

1. Save this code in a file named `test_water_reminder.py` in the same directory as your `water_reminder.py` file.

2. Run the tests using the following command:
   ```
   python -m unittest test_water_reminder.py
   ```

These tests use mocking to simulate external dependencies (like the Telegram API), allowing us to test our functions in isolation. The `setUp` method ensures that our global variables are reset before each test, preventing tests from interfering with each other.

To make these tests work with your actual `water_reminder.py` file, you might need to make some small adjustments:

1. Ensure that your main `water_reminder.py` file is structured in a way that allows importing individual functions.
2. You may need to add a `water_reminder.stop = False` at the beginning of your `water_reminder()` function, and check this value in the main loop to allow stopping the function in the test.

These tests provide rich examples of various scenarios, including valid and invalid inputs, command processing, daily resets, and the main app loop. They should help ensure that your water reminder app functions correctly across a wide range of use cases.

Would you like me to explain any of these tests in more detail, or discuss how to integrate them more closely with your existing code?