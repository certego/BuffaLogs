from enum import Enum

from rich.console import Console

console = Console()


class VLevel(str, Enum):
    quiet = "0"
    error = "1"
    info = "2"
    debug = "3"


class VPrint:

    def __init__(self, verbose_level: int = 2):
        self.level = verbose_level

    def __call__(self, level: str, *args, **kwargs):
        level = int(VLevel[level.lower()].value)
        if level > self.level:
            return  # Do Nothing
        console.print(*args, **kwargs)


vprint = VPrint()


def set_verbose_level(level: int | str):
    vprint.level = int(level)
