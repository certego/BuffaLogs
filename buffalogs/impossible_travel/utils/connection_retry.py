import logging
from typing import Tuple, Type

import backoff

logger = logging.getLogger(__name__)


def create_retry_decorator(
    retry_config: dict,
    exception_types: Tuple[Type[Exception], ...],
    operation_name: str = "Connection"
):
    """
    Create a retry decorator with exponential backoff based on configuration.

    :param retry_config: Dictionary containing retry configuration
    :param exception_types: Tuple of exception types to retry on
    :param operation_name: Name of the operation for logging
    :return: Configured backoff decorator
    """
    def on_giveup_handler(details):
        exception = details.get("exception")
        exception_msg = str(exception) if exception is not None else ""
        logger.error(
            f"{operation_name} failed after all retry attempts. "
            f"Last error: {exception_msg}"
        )

    def on_backoff_handler(details):
        exception = details.get("exception")
        exception_msg = str(exception) if exception is not None else ""
        logger.warning(
            f"{operation_name} attempt {details['tries']} failed. "
            f"Retrying in {details['wait']:.2f}s... "
            f"(elapsed: {details['elapsed']:.2f}s). "
            f"Error: {exception_msg}"
        )

    if not retry_config.get("enabled", True):
        return lambda func: func

    decorator_kwargs = {
        "wait_gen": backoff.expo,
        "exception": exception_types,
        "max_tries": retry_config.get("max_retries", 10),
        "max_time": retry_config.get("max_elapsed_time", 60),
        "base": retry_config.get("initial_backoff", 1),
        "max_value": retry_config.get("max_backoff", 30),
        "on_backoff": on_backoff_handler,
        "on_giveup": on_giveup_handler,
    }

    if retry_config.get("jitter", True):
        decorator_kwargs["jitter"] = backoff.full_jitter

    return backoff.on_exception(**decorator_kwargs)
