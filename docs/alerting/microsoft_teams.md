# Microsoft Teams Webhook Configuration Guide 

This guide outlines the steps to configure Microsoft Teams webhooks for receiving security alerts from BuffaLogs. 

> **Note**   
> This feature is **exclusively available for Microsoft Business Accounts**. Ensure you have the necessary permissions before proceeding.

## Prerequisites 
- Microsoft Business Account with **admin rights** to configure Teams channels.
- Access to the Teams channel where alerts will be sent.

---


<summary><strong>▶️ Step-by-Step Configuration</strong></summary>

### 1. Create an Incoming Webhook in Microsoft Teams

1. **Navigate to your Teams channel**:
   - Open the channel where alerts should be sent.
   - Click the **⋮ (More options)** button next to the channel name.
   - Select **Connectors** from the dropdown.


2. **Add the Incoming Webhook connector**:
   - Search for **Incoming Webhook** and click **Add**.
   - Provide a name for the webhook (e.g., `BuffaLogs Alerts`) and upload an optional icon.
   - Click **Create**.

3. **Copy the Webhook URL**:
   - A unique URL will be generated. **Copy this URL** immediately—it will not be shown again.

   [Microsoft Teams Offical Documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/assets/images/webhooks/webhook-url.png)

---

### 2. Configure `alerting.json`

1. **Paste the Webhook URL**:
   - Update the `alerting.json` file by adding the webhook URL to the `microsoftTeams` section.

   ```json
   {
     "microsoftteams": {
       "webhook_url": "https://example.webhook.office.com/webhookb2/.../IncomingWebhook/..."
     }
   }

> **Note**  
> Microsoft Teams may not provide quick notifications on mobile devices. It is recommended to use a desktop system for monitoring critical alerts.