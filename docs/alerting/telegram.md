# Configuring Telegram Alerter for BuffaLogs

<p><i>This document outlines the steps to configure <b>Telegram</b> alerter for BuffaLogs to receive alerts via Telegram Bot API.</i><p>

---

## Prerequisites

Before setting up the Telegram alerter, ensure the following:
- You have a Telegram account.
- You have created a Telegram bot using BotFather.
- BuffaLogs is installed and configured on your system.

---

## Steps to Implement

#### 1. Create a Telegram Bot
1. Open Telegram and search for **BotFather**.
2. Start a chat with BotFather and use the `/newbot` command to create a new bot.
3. Follow the instructions to set up your bot and obtain the **Bot Token**.

#### 2. Get the Chat ID
1. Start a chat with your bot in Telegram.
2. Use the Telegram API to get your chat ID by visiting the following URL in your browser:
    ```
    https://api.telegram.org/bot<your-bot-token>/getUpdates
    ```
3. Replace `<your-bot-token>` with the token you received from BotFather.
4. Look for the `chat` object in the response and note the `id` field.


#### 3. Update Configuration File
1. Open the BuffaLogs configuration file located at `config/buffalogs/alerting.json`.
2. Add or update the following JSON configuration with your Telegram bot details:

    ```json
    {
        "active_alerters": ["telegram"],
        "telegram": {
            "bot_token": "your-bot-token",
            "chat_ids": ["your-chat-id"]
        }
    }
    ```

3. Replace `"your-bot-token"` and `"your-chat-id"` with the values you obtained earlier.
4. Save the file.

---

## Testing the Setup

1. Make sure the Docker containers are up and running.
2. Trigger the tests using the following command in your terminal:
    ```bash
    ./manage.py test impossible_travel.tests.alerters.test_alert_telegram.TestTelegramAlerting
    ```
**Extra Note**

3. To get a real test alert message in your Telegram chat, add this code in `buffalogs/impossible_travel/tests/alerters/test_alert_telegram.py` :

    ```python
    def test_actual_alert(self):
        self.telegram_alerting.notify_alerts()
    ```

4. Check the specified Telegram chat to verify that the alert message has been received.