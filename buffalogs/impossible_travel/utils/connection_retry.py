import logging

import backoff
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from elasticsearch.exceptions import ConnectionTimeout

logger = logging.getLogger(__name__)


def es_connection_retry(max_tries=10, max_time=300):
    def giveup_handler(details):
        logger.error(
            f"Elasticsearch connection failed after {details['tries']} attempts. "
            f"Total elapsed time: {details['elapsed']:.2f}s"
        )

    def on_backoff_handler(details):
        logger.warning(
            f"Elasticsearch connection attempt {details['tries']} failed. "
            f"Retrying in {details['wait']:.2f}s... "
            f"(elapsed: {details['elapsed']:.2f}s)"
        )

    return backoff.on_exception(
        backoff.expo,
        (ESConnectionError, ConnectionTimeout, ConnectionError, TimeoutError),
        max_tries=max_tries,
        max_time=max_time,
        base=1,
        max_value=30,
        on_backoff=on_backoff_handler,
        giveup=giveup_handler,
    )
