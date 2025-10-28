# Django Management Command: `reset_user_risk_score`

## Description

The `reset_user_risk_score` management command allows administrators to reset or update the `risk_score` value for one or more users in the system.

This command can be used to:

- Reset all users’ risk scores to the default (`NO_RISK`)
- Update a specific user’s risk score
- Apply a specific risk score to all users

It is useful during testing, investigation cleanups, or bulk resets after risk assessments.

## Usage

Run the command from the root of your Django project:

```bash
./manage.py reset_user_risk_score [--username USERNAME] [--risk_score RISK_SCORE]
```

| Option         | Name       | Description                                                                                                   |
| -------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| `--username`   | Username   | (Optional) Username of the user whose `risk_score` should be updated. If not provided, all users are updated. |
| `--risk_score` | Risk Score | (Optional) Risk score value to assign. Defaults to `NO_RISK` if not specified.                                |

## Reset all users to default risk score

```bash
./manage.py reset_user_risk_score

```

## Update a specific user’s risk score

```bash
./manage.py reset_user_risk_score --username=john_doe --risk_score=HIGH_RISK
```

## Apply a uniform risk score to all users

```bash
./manage.py reset_user_risk_score --risk_score=MEDIUM_RISK
```
