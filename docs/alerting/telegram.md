# Telegram Alerting Integration for BuffaLogs

BuffaLogs supports sending security alerts directly to Telegram using a custom bot. This guide explains how to configure, deploy, and use the Telegram Bot for receiving alerts.

---

## Step 1: Create a Telegram Bot

To create a bot, follow these steps:

1. Open Telegram and search for [@BotFather](https://t.me/botfather).
2. Start a chat with BotFather and send the command: `/newbot`
3. Follow the prompts to give your bot a name and username.
4. Once created, you will receive a **bot token** — save this for later configuration.

---

## Step 2: Start the Bot and Get Your Chat ID

For security purposes only selected individual shall be allowed to recieve alerts,providing everyone access to the chat_id function can be harmful.
So,deploy this python script to get your chat_id
```python
import telebot

BOT_TOKEN = 'BOT_TOKEN'  # Replace with your actual bot token

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Welcome! Your chat ID is: {message.chat.id}")

bot.send_message()

bot.polling()
```

---

## Step 4: Configure BuffaLogs to Use Telegram

Edit your `alerting.json` to include:

```json
"telegram":{
        "bot_token":"BOT_TOKEN",
        "chat_ids" : ["CHAT_ID"]
    }
```
