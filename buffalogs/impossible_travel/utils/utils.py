import ipaddress

from celery.utils.log import get_task_logger
from impossible_travel.models import Config

logger = get_task_logger(__name__)


def check_ignored_ips(login_ip):
    config = Config.objects.all()[0]
    if login_ip in config.ignored_ips:
        return True
    for ip in config.ignored_ips:
        try:
            if ipaddress.ip_address(login_ip) in ipaddress.ip_network(ip):
                return True
        except ValueError:
            logger.error(f"IP {login_ip} is malformed. It will be ignored")
            return True
    return False
