import typer

app = typer.Typer()


@app.command()
def main(ds_name: str = typer.Argument(..., help="Name of the dataset")):
    """object-partitioning CLI is working!"""
    print(f"object-partitioning CLI is working with dataset: {ds_name}")


if __name__ == "__main__":
    app()
