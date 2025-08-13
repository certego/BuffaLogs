import csv
import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from buffacli.models import DataModel


class BaseExporter(ABC):

    def __init__(self, filename: Path):
        self.filename = filename

    @abstractmethod
    def export(self, model: DataModel):
        raise NotImplementedError


class JSONExporter(BaseExporter):

    def export(self, model: DataModel):
        json_content = model.json
        with open(self.filename, "w") as f:
            json.dump(json_content, f, indent=4)


class CSVExporter(BaseExporter):

    def export(self, model: DataModel):
        fieldnames = model.table.keys()
        with open(self.filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if isinstance(model.content, dict):
                writer.writerow(model.table)
                return
            table = model.table
            headers = table.keys()
            rows = list(zip(*[table[header] for header in headers]))
            for index in range(len(rows)):
                writer.writerow(dict(zip(headers, rows[index])))


options = {".csv": CSVExporter, ".json": JSONExporter}


def get_exporter(output_file: Path):
    export_class = options.get(output_file.suffix.lower())
    if export_class:
        return export_class(output_file)
