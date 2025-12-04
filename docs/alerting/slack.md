# Slack Integration for BuffaLogs

## Overview
BuffaLogs can send alerts to Slack channels using Incoming Webhooks. This integration allows you to receive real-time notifications about impossible travel detections.

## Setup Instructions

### 1. Create a Slack App
1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app (e.g., "BuffaLogs Alerts") and select your workspace

### 2. Configure Incoming Webhooks
1. In your app's settings, go to "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" to On
3. Click "Add New Webhook to Workspace"
4. Select the channel where you want to receive alerts
5. Copy the Webhook URL provided by Slack

### 3. Configure BuffaLogs
Add the following configuration to your `alerting.json`:
```json
{
    "slack": {
        "enabled": true,
        "webhook_url": "YOUR_WEBHOOK_URL_HERE",
        "channel": "#your-channel-name"
    }
}
```

## Testing
You can test your Slack integration using curl:
```bash
curl -X POST -H 'Content-type: application/json' --data '{"text":"Test message from BuffaLogs"}' YOUR_WEBHOOK_URL_HERE
```