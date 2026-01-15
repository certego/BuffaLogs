import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from impossible_travel.views import utils

read_config, write_config = utils.get_config_read_write("ingestion.json")


@require_http_methods(["GET"])
def get_ingestion_sources(request):
    config = read_config()
    ingestors = [
        {"source": ingestor, "fields": config[ingestor]["__custom_fields__"]}
        for ingestor, value in config.items()
        if isinstance(value, dict) and "__custom_fields__" in value
    ]
    return JsonResponse(ingestors, json_dumps_params={"default": str}, safe=False)


@require_http_methods(["GET"])
def get_active_ingestion_source(request):
    config = read_config()
    source = config["active_ingestion"]
    context = {
        "source": source,
        "fields": dict((field, config[source][field]) for field in config[source]["__custom_fields__"]),
    }
    return JsonResponse(context, json_dumps_params={"default": str})


def ingestion_source_config(request, source):
    try:
        ingestion_config = read_config(key=source)
    except KeyError:
        return JsonResponse({"message": f"Unsupported ingestion source - {source}"}, status=400)

    if request.method == "GET":
        context = {
            "source": source,
            "fields": dict((field, ingestion_config[field]) for field in ingestion_config["__custom_fields__"]),
        }
        return JsonResponse(context, json_dumps_params={"default": str})

    if request.method == "POST":
        config_update = json.loads(request.body.decode("utf-8"))
        error_fields = [field for field in config_update.keys() if field not in ingestion_config["__custom_fields__"]]
        if any(error_fields):
            return JsonResponse(
                {"message": f"Unexpected configuration fields - {error_fields}"},
                status=400,
            )
        ingestion_config.update(config_update)
        write_config(source, ingestion_config)
        return JsonResponse({"message": "Update successful"}, status=200)
