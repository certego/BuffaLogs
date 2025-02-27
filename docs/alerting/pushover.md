# Adding a Pushover Alerter to BuffaLogs

This document outlines the steps to add a **Pushover** alerter to BuffaLogs to receive alerts via the [Pushover](https://pushover.net/api) notification service.

---

## Steps to Implement

### 1. Create a Pushover Account
- Sign up at https://pushover.net.
- Obtain your **User Key** (this identifies your account).
- Create a new **Application** in Pushover API.
- Obtain the **API Token** for this application.

---

### 2. Update Configuration File
- Update `config/buffalogs/alerting.json` with Pushover details:

```json
{
    "active_alerter": "pushover",
    "pushover": {
        "api_key": "your-pushover-api-token",
        "user_key": "your-pushover-user-key"
    }
}
```

---

