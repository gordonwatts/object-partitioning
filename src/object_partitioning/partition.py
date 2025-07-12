import awkward as ak
import typer

from object_partitioning.scan_ds import collect_object_counts

app = typer.Typer()


@app.command()
def main(ds_name: str = typer.Argument(..., help="Name of the dataset")):
    """object-partitioning CLI is working!"""

    counts = collect_object_counts(ds_name)

    ak.to_parquet(counts, "object_counts.parquet")


if __name__ == "__main__":
    app()
