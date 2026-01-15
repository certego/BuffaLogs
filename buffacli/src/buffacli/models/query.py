from buffacli.models.base import DataModel


class Query(DataModel):

    custom_mappings = {}

    def __init__(self, content: dict | list[dict], omit: list = None, mappings: dict[str, str] = None, fields: str = None):
        if not (isinstance(content, list) or isinstance(content, dict)):
            raise TypeError(f"{self.__class__.__name__} got content of type {type(content)}. Expected list or dict object")
        self.content = content
        self.omit = omit or []
        self.fields = fields or self.__class__.fields
        if mappings:
            self.custom_mappings = mappings

    @property
    def table(self):
        if isinstance(self.content, list):
            data = {}
            for row in self.content:
                for key, value in row.items():
                    if (key not in self.fields) or (key in self.omit):
                        continue
                    mapped_key = self.custom_mappings.get(key, key)
                    column = data.get(mapped_key, [])
                    column.append(value)
                    data[mapped_key] = column

        elif isinstance(self.content, dict):
            data = dict((self.custom_mappings.get(key, key), []) for key in self.fields if key not in self.omit)
            for key, value in self.content.items():
                mapped_key = self.custom_mappings.get(key, key)
                data[mapped_key].append(value)
        return data

    @property
    def json(self):
        if isinstance(self.content, list):
            data = []
            for row in self.content:
                row_copy = row.copy()
                for key in row.keys():
                    if (key not in self.fields) or (key in self.omit):
                        row_copy.pop(key)
                        continue
                    mapped_key = self.custom_mappings.get(key)
                    if mapped_key:
                        value = row_copy.pop(key)
                        row_copy[mapped_key] = value
                data.append(row_copy)

        elif isinstance(self.content, dict):
            data = {}
            for key in self.content:
                if (key not in self.fields) or (key in self.omit):
                    continue
                mapped_key = self.custom_mappings.get(key, key)
                data[mapped_key] = self.content[key]
        return data


class AlertQuery(Query):
    fields = [
        "rule_name",
        "triggered_by",
        "country",
        "created",
        "updated",
        "is_vip",
        "severity_type",
    ]

    custom_mappings = {
        "rule_name": "alert_type",
    }


class LoginQuery(Query):
    fields = [
        "user",
        "created",
        "updated",
        "timestamp",
        "latitude",
        "longituted",
        "country",
        "user_agent",
        "index",
        "ip",
        "event_id",
    ]


class UserQuery(Query):
    fields = ["risk_score", "created", "updated"]


class UserIPQuery(Query):
    fields = ["created", "updated", "user"]
