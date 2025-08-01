from buffacli.formatters import FormatOptions
from rich.console import Console


class Render:

    def __init__(self, formatter: FormatOptions, mode=None, page_size=None):
        self.formatter = formatter
        self.mode = mode
        self.page_size = page_size

    def less(self, formatted_content):
        "Display in unix less mode."
        with self.console.pager():
            self.console.print(formatted_content)

    def shell(self, formatted_content):
        pass

    def paginate(self, formatted_content, page_size: int, caller: callable):
        """
        Display paginated API calls.

        formatted_content : Formatted API response
        page_size : number of objects per page
        caller : callable that returns the next page
        """
        pass

    def __call__(self, content, mode: str = "", **formatter_kwargs):
        console = Console()
        if not console.is_terminal:
            print(content.raw)
            return

        self.console = console
        mode = mode or self.mode
        formatted_content = self.formatter(content, **formatter_kwargs)
        match mode.lower():
            case "less":
                self.less(formatted_content)
            # case "shell":
            #    self.shell(formatted_content)
            # case "paginate":
            #    self.paginate(formatted_content)
            case _:
                self.console.print(formatted_content)


def make_renderable(format_option: FormatOptions, mode: str = "less", page_size: int = 50):
    "Return a render object."
    render = Render(format_option.formatter, mode=mode, page_size=page_size)
    format_option.print = render
    return format_option
