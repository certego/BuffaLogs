import json


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
