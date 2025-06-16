# Adding RocketChat Alerter to BuffaLogs

This document outlines the steps to add **RocketChat** alerter to BuffaLogs.
---

## Steps to Implement

### 1. Create a Webhook URL
- Go to Administration -> Integrations -> New Integration
- Choose Incoming Webhook
- Set
    - Username from which alerts will be posted
    - Channel where alerts will be posted
    - Check Enabled
- Save and copy the Webhook URL
---

### 2. Update Configuration File
- Update `config/buffalogs/alerting.json` with RocketChat WebHook details:

```json
{
    "rocketchat" : {
        "webhook_url" : "YOUR_WEBHOOK_URL",
        "username" : "YOUR_USERNAME",
        "channel" : "#YOUR_CHANNEL"
    }
}
```

---