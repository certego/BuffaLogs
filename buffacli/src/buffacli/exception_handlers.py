from functools import wraps
from typing import Callable, Type

from requests import exceptions
from rich.console import Console
from rich.panel import Panel
import typer
from typer import Typer

from buffacli.globals import vprint

ExceptionType = Type[Exception]
ExceptionHandlingCallback = Callable[[Exception], int]


class ExceptionHandler:
    def __init__(self, error_handlers: dict[ExceptionType, ExceptionHandlingCallback]):
        self.error_handlers = error_handlers

    def __call__(self, func: callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                try:
                    handler = self.error_handlers[type(e)]
                    exit_code = handler(e)
                    raise typer.Exit(code=exit_code)
                except KeyError:
                    raise e
            else:
                return result

        return wrapper


def request_generic_handler(exc: exceptions.RequestException):
    vprint(
        "debug",
        Panel(str(exc), title="[bold red]Request Error[/bold red]", style="bold"),
    )
    vprint("error", "Error: Request Failed")
    return 1


request_exception_handler = ExceptionHandler(
    error_handlers={
        exceptions.ConnectionError: request_generic_handler,
        exceptions.Timeout: request_generic_handler,
        exceptions.HTTPError: request_generic_handler,
        exceptions.SSLError: request_generic_handler,
        exceptions.RequestException: request_generic_handler,
    }
)
