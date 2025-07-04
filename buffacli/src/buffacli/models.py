import json

from buffacli import config
from yarl import URL


class DataModel:
    root = URL(config.get_buffalogs_url())

    @property
    def table(self):
        raise NotImplementedError

    @property
    def json(self):
        return self.content

    @property
    def yaml(self):
        raise NotImplementedError

    @property
    def tree(self):
        raise NotImplementedError

    @property
    def raw(self):
        return json.dumps(self.content)


class AlertType(DataModel):

    def __init__(self, content: dict, include_description: bool = False):
        self.content = content
        self.include_description = include_description

    @property
    def table(self):
        structure = {"alert_type": [], "description": []}
        for alert_type in self.content:
            structure["alert_type"].append(alert_type["alert_type"])
            structure["description"].append(alert_type["description"])

        if not self.include_description:
            structure.pop("description")

        return structure


class Ingestion(DataModel):

    def __init__(self, content: dict | list[dict]):
        self.content = content

    @property
    def table(self):
        if isinstance(self.content, dict):
            structure = {"fields": [], "": []}
            for key, value in self.content["fields"].items():
                structure["fields"].append(key)
                structure[""].append(value)
        elif isinstance(self.content, list):
            structure = {}
            structure["sources"] = [data["source"] for data in self.content]
            structure["fields"] = [data["fields"] for data in self.content]
        else:
            raise TypeError(f"Expected type List or Dict for content, got {type(self.content)}")
        return structure
