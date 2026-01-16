import csv
import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from buffacli.globals import vprint
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
        vprint("info", "Exporting  data to {self.filename}...", end="")
        with open(self.filename, "w") as f:
            json.dump(json_content, f, indent=4)
        vprint("debug", f"Row Count: {1 if isinstance(json_content, dict) else len(json_content)}")


class CSVExporter(BaseExporter):
    def export(self, model: DataModel):
        fieldnames = list(model.table.keys())
        vprint("info", f"Exporting  data to {self.filename}...")
        vprint("debug", f"CSV Headers: {fieldnames}")
        with open(self.filename, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if isinstance(model.content, dict):
                writer.writerow(model.table)
                vprint("debug", "CSV Row Count: 1")
                return
            table = model.table
            headers = table.keys()
            rows = list(zip(*[table[header] for header in headers]))
            for index in range(len(rows)):
                writer.writerow(dict(zip(headers, rows[index])))
            vprint("debug", f"CSV Row Count: {len(rows)}")


options = {".csv": CSVExporter, ".json": JSONExporter}


def get_exporter(output_file: Path):
    export_class = options.get(output_file.suffix.lower())
    if export_class:
        return export_class(output_file)
