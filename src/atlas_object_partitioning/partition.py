import typer

from atlas_object_partitioning.scan_ds import collect_object_counts
from atlas_object_partitioning.histograms import (
    compute_bin_boundaries,
    write_bin_boundaries_yaml,
    build_nd_histogram,
    write_histogram_pickle,
    top_bins,
    bottom_bins,
    print_bin_table,
)

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
    # ak.to_parquet(counts, output_file)

    simple_boundaries = compute_bin_boundaries(counts)
    write_bin_boundaries_yaml(simple_boundaries, "bin_boundaries.yaml")

    hist = build_nd_histogram(counts, simple_boundaries)
    write_histogram_pickle(hist, "histogram.pkl")

    top = top_bins(hist, n=10)
    bottom = bottom_bins(hist, n=10)
    print_bin_table(top, "Top 10 bins")
    print_bin_table(bottom, "Least 10 bins")


if __name__ == "__main__":
    app()
