# Adding Mattermost Alerter to BuffaLogs

This document outlines the steps to add **Mattermost** alerter to BuffaLogs.
---

## Steps to Implement

### 1. Incoming Webhook Setup
- Go to Main Menu → Integrations → Incoming Webhooks
- Click "Add Incoming Webhook"
- Select the channel where alerts will be published
- Give it a name like "BuffaLogs Alert Bot"
- Click Save — you'll get a Webhook URL.
- Also to use the username you just set-up for your alerts
    - Go to System Console → Integrations → Integration Management
    - Set "Enable integrations to override usernames" to True

---
### 3. Update Configuration File
- Update `config/buffalogs/alerting.json` with Mattermost WebHook details:

```json
{
    "active_alerter": "mattermost",
    "mattermost": {
        "webhook_url": "your-webhook-url",
        "username" : "your-username"
    }
}
```

---