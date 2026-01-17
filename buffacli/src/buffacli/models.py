import json

from yarl import URL

from buffacli import config


class DataModel:
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
            structure["fields"] = [", ".join(data["fields"]) for data in self.content]
        else:
            raise TypeError(f"Expected type List or Dict for content, got {type(self.content)}")
        return structure


class Alerters(DataModel):
    def __init__(self, content: dict | list[dict]):
        if isinstance(content, list):
            self.content = [alerter for alerter in content if alerter["alerter"] != "dummy"]
        elif isinstance(content, dict):
            self.content = content
        else:
            raise TypeError(f"Expected type list or dict for content, got {type(content)}")

    @property
    def table(self):
        if isinstance(self.content, dict):
            structure = {"fields": [], "": []}
            for key, value in self.content["fields"].items():
                structure["fields"].append(key)
                structure[""].append(value)
        elif isinstance(self.content, list):
            structure = {}
            structure["alerter"] = [data["alerter"] for data in self.content]
            structure["fields"] = [", ".join(data["fields"]) for data in self.content]
        else:
            raise TypeError(f"Expected type List or Dict for content, got {type(self.content)}")
        return structure
