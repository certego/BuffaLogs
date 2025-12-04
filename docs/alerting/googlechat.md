# Adding a GoogleChat Alerter to BuffaLogs

This document outlines the steps to add a **GoogleChat** alerter to BuffaLogs to receive alerts via the GoogleChat Webhooks.
---

## Steps to Implement

### 1. Create a Google Chat Space (if you don’t have one)
- Go to https://chat.google.com
- Create or open an existing Space (a group chat or channel)
---

### 2. Add a Webhook to the Space
- In the space → Apps & Integrations → Webhooks
- Click "Add webhook"
- Give it a name like "BuffaLogs Alert Bot"
- Click Save — you'll get a Webhook URL like:
```
https://chat.googleapis.com/v1/spaces/AAAAxyz/messages?key=abc123&token=def456
```

---
### 3. Update Configuration File
- Update `config/buffalogs/alerting.json` with GoogleChat WebHook details:

```json
{
    "active_alerter": "googlechat",
    "googlechat": {
        "webhook_url": "your-webhook-url",
    }
}
```

---