# Adding a Slack Alerter to BuffaLogs

This document outlines the steps to add a **Slack** alerter to BuffaLogs to receive alerts via the [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks).

---

## Steps to Implement

### 1. Create a Webhook URL
- Create a new workspace on your Slack,if you don't have one already.
- Create an app from [Slack API: Applications](https://api.slack.com/apps?new_app=1)
- Choose **From Scratch** and give your app a name.
- Select the Slack workspace where you want to install the app.
- Once created, navigate to **Incoming Webhooks** under the "Features" section.
- Enable **Incoming Webhooks**.
- Click **Add New Webhook to Workspace** and choose the channel where alerts should be posted.
- Copy the generated **Webhook URL** — you’ll need this in the BuffaLogs configuration.
---

### 2. Update Configuration File
- Update `config/buffalogs/alerting.json` with Slack WebHook details:

```json
{
    "active_alerter": "slack",
    "slack": {
        "webhook_url": "your-webhook-url",
    }
}
```

---
