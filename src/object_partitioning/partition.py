import awkward as ak
import typer

from object_partitioning.scan_ds import collect_object_counts

app = typer.Typer()


@app.command()
def main(
    ds_name: str = typer.Argument(..., help="Name of the dataset"),
    output_file: str = typer.Option(
        "object_counts.parquet",
        "--output",
        "-o",
        help="Output file name for the object counts parquet file.",
    ),
    n_files: int = typer.Option(
        1,
        "--n-files",
        "-n",
        help="Number of files to use (0 for all files)",
    ),
):
    """object-partitioning CLI is working!"""
    counts = collect_object_counts(ds_name, n_files=n_files)
    ak.to_parquet(counts, output_file)


if __name__ == "__main__":
    app()
