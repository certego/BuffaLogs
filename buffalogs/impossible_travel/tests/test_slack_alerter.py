import pytest
from unittest.mock import patch, MagicMock
from buffalogs.impossible_travel.alerting.slack_alerter import SlackAlerter


@pytest.fixture
def slack_config():
    return {
        "webhook_url": "https://hooks.slack.com/services/TEST/TEST/TEST",
        "channel": "#test-channel",
    }


@pytest.fixture
def alert_data():
    return {
        "user": "test_user",
        "timestamp": "2025-02-28T12:00:00Z",
        "location1": "New York",
        "location2": "Tokyo",
    }


def test_slack_alerter_initialization(slack_config):
    alerter = SlackAlerter(slack_config)
    assert alerter.webhook_url == slack_config["webhook_url"]
    assert alerter.channel == slack_config["channel"]


def test_slack_alerter_missing_webhook():
    with pytest.raises(ValueError):
        SlackAlerter({})


@patch("requests.post")
def test_send_alert_success(mock_post, slack_config, alert_data):
    mock_post.return_value = MagicMock(status_code=200)
    alerter = SlackAlerter(slack_config)
    assert alerter.send_alert(alert_data) is True
    mock_post.assert_called_once()


@patch("requests.post")
def test_send_alert_failure(mock_post, slack_config, alert_data):
    mock_post.side_effect = Exception("Connection error")
    alerter = SlackAlerter(slack_config)
    assert alerter.send_alert(alert_data) is False
