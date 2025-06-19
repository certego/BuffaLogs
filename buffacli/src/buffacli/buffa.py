import typer

app = typer.Typer()


@app.command()
def main():
    print("Hello World")


if __name__ == "__main__":
    app()
