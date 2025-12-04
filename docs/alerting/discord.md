# Adding a Discord Alerter to BuffaLogs

This document outlines the steps to add a **Discord** alerter to BuffaLogs to receive alerts via the Discord Webhooks.
---

## Steps to Implement

### 1. Create a Webhook URL
- Create a server on Discord if you don't have one already.
- If you already have a server you should be an admin to setup webhooks.
- Go to the server settings->integrations->webhooks
- Create webhook url for your desired channel.
---

### 2. Update Configuration File
- Update `config/buffalogs/alerting.json` with Discord WebHook details:

```json
{
    "active_alerter": "discord",
    "discord": {
        "webhook_url": "your-webhook-url",
    }
}
```

---