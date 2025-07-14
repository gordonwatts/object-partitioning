import awkward as ak
import typer

from atlas_object_partitioning.scan_ds import collect_object_counts

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
    servicex_name: str = typer.Option(
        None,
        "--servicex-name",
        help="Name of the ServiceX instance (default taken from `servicex.yaml` file)",
    ),
    ignore_cache: bool = typer.Option(
        False,
        "--ignore-cache",
        help="Ignore servicex local cache and force fresh data SX query.",
    ),
):
    """atlas-object-partitioning CLI is working!"""
    counts = collect_object_counts(
        ds_name,
        n_files=n_files,
        servicex_name=servicex_name,
        ignore_local_cache=ignore_cache,
    )
    ak.to_parquet(counts, output_file)


if __name__ == "__main__":
    app()
