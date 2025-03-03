# BuffaLogs Telegram Alert Setup Guide

##  Table of Contents
1. [Prerequisites](#prerequisites)
2. [Create Your Bot](#create-your-bot)
3. [Get Chat ID](#get-chat-id)
4. [Configuration](#configuration)
5. [Test Alerts](#test-alerts)
6. [Troubleshooting](#troubleshooting)
7. [Resources](#resources)

---
<a name="prerequisites"></a>
## Prerequisites
1. **Telegram Account** ([Sign up](https://telegram.org/))
2. **Setup BuffaLogs on your machine**. ([BuffaLogs GitHub](https://github.com/certego/BuffaLogs))


---
<a name="create-your-bot"></a>
## **Bot Creation Workflow**

### 1. **Create Bot via @BotFather**

- Open Telegram and search for **@BotFather** (the official bot for creating new bots).
- Start a chat with **@BotFather**.
- Send the command `/newbot`.
- Follow the prompts to set:
  - **Bot Name:** BuffaLogs Alert System
  - **Username:** BuffaLogsAlertBot
- You’ll receive a message containing your bot token. It will look something like this:

```
Your bot is now live! You can use the following token to access the HTTP API:
1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ-abcde
```

**Save the token securely.** This token is crucial for interacting with your bot and should be kept private.


---
<a name="get-chat-id"></a>
### 2. **Obtain Chat ID**

#### **Method 1: Using @userinfobot (Recommended)**

- Open Telegram and search for **@userinfobot**.
- Start a chat and send the command `/start`.
- You’ll receive a response containing your chat ID, which will look like this:

```text
ID: 123456789
First Name: John
Last Name: Doe
Username: johndoe
Language: en
```

The **ID** is your **chat ID**.

#### **Method 2: API Request**

If you prefer using the Telegram API, you can fetch the chat ID using the following command:

```bash
curl -s "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates" | jq '.result[].message.chat.id'
```

Make sure to replace `<YOUR_BOT_TOKEN>` with your actual bot token. The response will give you the chat ID.



---
<a name="configuration"></a>
##  **Configuration**

### **Config File Setup**

You can configure the Telegram alerting by editing the `alerting.json` file.

 **alerting.json Example** Located in [`config/buffalogs/alerting.json`](https://github.com/certego/BuffaLogs/blob/main/config/buffalogs/alerting.json)

```json
{
    "active_alerter": "telegram",
    "telegram": {
        "api_base_url": "https://api.telegram.org",
        "bot_token": "your_bot_token",   // Replace with your Telegram bot token from BotFather
        "chat_id": "your_chat_id"       // Replace with your obtained chat ID from @userinfobot
    }
}
```

### Steps:
1. Replace **`your_bot_token`** with the token you received from **BotFather**.
2. Replace **`your_chat_id`** with the chat ID you obtained from **@userinfobot** or via the API.


---
<a name="test-alerts"></a>
## **Executing the Test**  

To verify that Telegram alerts are functioning correctly, execute the following script in the Django shell:  

```python
from impossible_travel.alerting.telegram_alerting import TelegramAlerting

# Define Telegram configuration
telegram_config = {
    "api_base_url": "https://api.telegram.org",
    "bot_token": "YOUR_BOT_TOKEN",  # Replace with the actual bot token
    "chat_id": "YOUR_CHAT_ID"       # Replace with the actual chat ID
}

# Initialize and send the alert
telegram_alerting = TelegramAlerting(telegram_config)
telegram_alerting.notify_alerts()
```
**Expected Outcome**  

Upon execution, the Telegram bot should send a notification message to the specified chat ID. If no message is received, consider the following:  

- Verify that the **bot token** and **chat ID** are correct.  
- Ensure the bot has not been blocked in the Telegram chat.  
- Check the Django logs for any errors.  

---
<a name="troubleshooting"></a>
## Troubleshooting

### Common Issues Table

| Symptom | Diagnosis | Solution |
|---------|-----------|----------|
| 401 Unauthorized | Invalid bot token | Regenerate token via @BotFather |
| 400 Bad Request | Invalid chat_id | Re-validate using /getUpdates |
| Message not delivered | Bot blocked by user | Check chat history with bot |
| Partial formatting | Markdown syntax error | Use double-escaped characters |


---
<a name="resources"></a>
## Resources

- [Official Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [Markdown Formatting Guide](https://core.telegram.org/bots/api#markdown-style)