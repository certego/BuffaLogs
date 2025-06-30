import json
import os
from typing import Any, Dict, Generator, List, Optional

from django.conf import settings
from django.utils import timezone
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.helpers.errors import BulkIndexError

# Utils for all the ingestion sources


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
        raise FileNotFoundError(f"Test data file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON format in file: {path}", e.doc, e.pos)


def _bulk_gendata(index: str, docs: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
    """
    Generator to yield documents in the format required by bulk().

    :param index: Index name
    :type index: str
    :param docs: List of documents
    :type docs: List[Dict[str, Any]]

    :yield: Formatted document for bulk indexing
    """
    for doc in docs:
        yield {"_op_type": "index", "_index": index, "_source": doc}


# Utils for the ELASTICSEARCH ingestion source


def elasticsearch_load_template(name: str, es: Elasticsearch) -> dict:
    """
    Load an Elasticsearch index template from a JSON file and upload it to Elasticsearch.

    :param name: Name of the template file (without .json extension)
    :type name: str
    :param es: Elasticsearch client instance
    :type es: Elasticsearch

    :return: Response from Elasticsearch after uploading the template
    :rtype: dict
    """
    path = os.path.join(settings.CERTEGO_BUFFALOGS_CONFIG_PATH, "elasticsearch", f"{name}.json")
    with open(path, "r", encoding="utf-8") as file:
        template_data = json.load(file)

    response = es.indices.put_index_template(name=name, body=template_data)
    if not response.get("acknowledged", False):
        raise RuntimeError(f"Failed to upload template '{name}'. Response: {response}")

    return response


def elasticsearch_write_bulk(
    es: Elasticsearch,
    index_prefix: str,
    documents: List[Dict[str, Any]],
) -> None:
    """
    Writes a list of documents to Elasticsearch using bulk indexing.

    :param es: Elasticsearch client
    :type es: Elasticsearch
    :param index_prefix: Prefix for the index name (e.g., "cloud-*")
    :type index_prefix: str
    :param documents: List of documents to index
    :type documents: List[Dict[str, Any]]
    """
    now = timezone.now()
    prefix_cleaned = index_prefix.strip().removesuffix("-*")
    index_name = f"{prefix_cleaned}-test_data-{now.year}-{now.month}-{now.day}"

    if not es.indices.exists(index=index_name):
        try:
            es.indices.create(index=index_name)
        except Exception as e:
            raise RuntimeError(f"Failed to create index '{index_name}': {e}")

    try:
        bulk(es, _bulk_gendata(index_name, documents))
    except BulkIndexError as e:
        raise BulkIndexError(f"Bulk indexing failed: {e}", e.errors)


def elasticsearch_parse_index_patterns(index_pattern_string: str) -> List[str]:
    """
    Parse a comma-separated string of Elasticsearch index patterns and return
    cleaned base names, removing wildcard patterns like '*' or '-*'.

    Example:
        Input:  'cloud-*, fw-proxy-*'
        Output: ['cloud', 'fw-proxy']

    :param index_pattern_string: Comma-separated index patterns (e.g., 'cloud-*,fw-proxy-*')
    :return: List of cleaned index base names
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
