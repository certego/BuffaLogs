import json
from pathlib import Path

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_http_methods


def read_config(source_name: str | None = None):
    config_path = Path(settings.CERTEGO_BUFFALOGS_CONFIG_PATH) / "buffalogs/ingestion.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        if source_name:
            return config[source_name]
        return config


def write_ingestion_config(source_name: str, ingestion_config: dict[str, str]):
    config_path = Path(settings.CERTEGO_BUFFALOGS_CONFIG_PATH) / "buffalogs/ingestion.json"
    config = read_config()
    config[source_name] = ingestion_config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(f, config, indent=2)


@require_http_methods(["GET"])
def get_ingestion_sources(request):
    config = read_config()
    active_ingestion = config.pop("active_ingestion")
    ingestors = [{"source": ingestor, "fields": config[ingestor]["__custom_fields__"]} for ingestor in config.keys()]
    return JsonResponse(ingestors, json_dumps_params={"default": str}, safe=False)


@require_http_methods(["GET"])
def get_active_ingestion_source(request):
    config = read_config()
    source = config["active_ingestion"]
    context = {"source": source, "fields": dict((field, config[source][field]) for field in config[source]["__custom_fields__"])}
    return JsonResponse(context, json_dumps_params={"default": str})


def ingestion_source_config(request, source):
    try:
        ingestion_config = read_config(source)
    except KeyError:
        return JsonResponse({"message": f"Unsupported ingestion source - {source}"}, status=400)

    if request.method == "GET":
        context = {"source": source, "fields": dict((field, ingestion_config[field]) for field in ingestion_config["__custom_fields__"])}
        return JsonResponse(context, json_dumps_params={"default": str})

    if request.method == "POST":
        config_update = json.loads(request.body.decode("utf-8"))
        error_fields = [field for field in config_update.keys() if field not in ingestion_config["__custom_fields__"]]
        if any(error_fields):
            return JsonResponse({"message": f"Unexpected configuration fields - {error_fields}"}, status=400)
        else:
            ingestion_config.update(config_update)
            write_ingestion_config(source, ingestion_config)
            return JsonResponse({"message": "Update successful"}, status=200)
