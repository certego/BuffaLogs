import json
import os
from typing import Any, Dict, Generator, List
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk as es_bulk
from elasticsearch.helpers.errors import BulkIndexError
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk as os_bulk

# -------------------- Config --------------------


def load_ingestion_config_data() -> dict:
    """
    Load the ingestion configuration from the config file.

    :return: Parsed ingestion configuration as a dictionary
    :rtype: dict
    """
    path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "buffalogs/ingestion.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in config file: {path}", e.doc, e.pos)


def load_template_data(template_name: str) -> dict:
    """
    Load an index template JSON from disk.

    :param template_name: Name of the template file (without .json)
    :type template_name: str

    :return: Template JSON data as dict
    :rtype: dict
    """
    path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "elasticsearch", f"{template_name}.json")
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Template file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in template file: {path}", e.doc, e.pos)


# -------------------- Bulk Utils -------------------- #


def _bulk_gendata(index: str, docs: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
    """
    Generator to yield documents for bulk indexing.

    :param index: Index name
    :type index: str
    :param docs: List of documents
    :type docs: List[Dict[str, Any]]

    :yield: Document formatted for bulk API
    """
    for doc in docs:
        yield {"_op_type": "index", "_index": index, "_source": doc}


def bulk_write_documents(client: Any, index_prefix: str, documents: List[Dict[str, Any]], refresh: bool = True, create_if_missing: bool = True) -> None:
    """
    Index documents in bulk to Elasticsearch or OpenSearch.

    :param client: Elasticsearch or OpenSearch client
    :type client: Elasticsearch/OpenSearch
    :param index_prefix: Index prefix (e.g., "cloud-*")
    :type index_prefix: str
    :param documents: Documents to write
    :type documents: List[Dict[str, Any]]
    :param refresh: Whether to refresh after indexing (default: True)
    :type refresh: bool
    :param create_if_missing: Create index if it doesn't exist (ES only) (default: True)
    :type create_if_missing: bool
    """
    now = timezone.now()
    prefix_cleaned = index_prefix.strip().removesuffix("-*")
    index_name = f"{prefix_cleaned}-test_data-{now.year}-{now.month}-{now.day}"

    if create_if_missing and isinstance(client, Elasticsearch):
        if not client.indices.exists(index=index_name):
            try:
                client.indices.create(index=index_name)
            except Exception as e:
                raise RuntimeError(f"Failed to create index '{index_name}': {e}")

    try:
        if isinstance(client, Elasticsearch):
            es_bulk(client, _bulk_gendata(index_name, documents), refresh=refresh)
        else:
            os_bulk(client, _bulk_gendata(index_name, documents), refresh=refresh)
    except BulkIndexError as e:
        raise BulkIndexError(f"Bulk indexing failed: {e}", e.errors)


# -------------------- Template Upload --------------------


def upload_index_template(client: Any, template_name: str, template_body: dict) -> dict:
    """
    Upload an index template to Elasticsearch or OpenSearch

    :param client: Elasticsearch or OpenSearch client
    :type client: Elasticsearch/OpenSearch
    :param template_name: Template name
    :type template_name: str
    :param template_body: Parsed template body (JSON)
    :type template_body: dict

    :return: Response from server
    :rtype: dict
    """
    response = client.indices.put_index_template(name=template_name, body=template_body)
    if not response.get("acknowledged", False):
        raise RuntimeError(f"Failed to upload template '{template_name}'. Response: {response}")
    return response


# -------------------- Client Factories --------------------


def opensearch_create_client(config: dict) -> OpenSearch:
    """
    Create and return an OpenSearch client.

    :param config: OpenSearch configuration (must include 'url', 'username', 'password')
    :type config: dict

    :return: OpenSearch client instance
    :rtype: OpenSearch
    """
    parsed = urlparse(config["url"])
    return OpenSearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port}],
        http_auth=(config["username"], config["password"]),
        timeout=config.get("timeout", 30),
        use_ssl=(parsed.scheme == "https"),
        verify_certs=False,
    )


def elasticsearch_create_client(config: dict) -> Elasticsearch:
    """
    Create and return an Elasticsearch client.

    :param config: Elasticsearch configuration
    :type config: dict

    :return: Elasticsearch client instance
    :rtype: Elasticsearch
    """
    parsed = urlparse(config["url"])
    return Elasticsearch(
        hosts=[{"host": parsed.hostname, "port": parsed.port}],
        http_auth=(config["username"], config["password"]),
        timeout=config.get("timeout", 30),
        use_ssl=(parsed.scheme == "https"),
        verify_certs=False,
    )


# -------------------- Index Pattern Parser --------------------


def parse_index_patterns(index_pattern_string: str) -> List[str]:
    """
    Parse a comma-separated string of index patterns and return base names.

    Example:
        Input:  'cloud-*, fw-proxy-*'
        Output: ['cloud', 'fw-proxy']

    :param index_pattern_string: Comma-separated index patterns
    :type index_pattern_string: str

    :return: List of cleaned base names
    :rtype: List
    """
    patterns = index_pattern_string.split(",")
    cleaned = []

    for p in patterns:
        p = p.strip()
        if not p:
            continue
        if p.endswith("-*"):
            cleaned.append(p[:-2])
        elif p.endswith("*"):
            cleaned.append(p[:-1])
        else:
            cleaned.append(p)
    return cleaned
