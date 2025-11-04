from typing import List
import awkward as ak
import typer

from atlas_object_partitioning.histograms import (
    bottom_bins,
    build_nd_histogram,
    compute_bin_boundaries,
    print_bin_table,
    top_bins,
    write_bin_boundaries_yaml,
    write_histogram_pickle,
)
from atlas_object_partitioning.scan_ds import collect_object_counts

app = typer.Typer()


@app.command()
def main(
    ds_name: str = typer.Argument(..., help="Name of the dataset"),
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file name for the object counts parquet file. If not provided, will not "
        "save to file.",
    ),
    n_files: int = typer.Option(
        1,
        "--n-files",
        "-n",
        help="Number of files in dataset to scan for object counts (0 for all files)",
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
    ignore_axes: List[str] = typer.Option(
        [],
        "--ignore-axes",
        help="List of axes to ignore when computing bin boundaries. Specify repeatedly for "
        "multiple axes.",
    ),
):
    """Use counts of PHYSLITE objects in a rucio dataset to determine skim binning.

    - Each *axis* is a count of PHYSLITE objects (muons, electrons, jets, etc).

    - Looks at each axis and tries to divide the counts into 4 bins of equal #s of events.

    - Then sub-divides each bin of axis 1 by axis 2 and axis 3 etc (making a
      n-dimensional histogram).

    - Saves the binning and histogram to files.

    - Prints out a table with the 10 largest and smallest bins.
    """
    counts = collect_object_counts(
        ds_name,
        n_files=n_files,
        servicex_name=servicex_name,
        ignore_local_cache=ignore_cache,
    )
    if output_file is not None:
        ak.to_parquet(counts, output_file)

    simple_boundaries = compute_bin_boundaries(counts, ignore_axes=ignore_axes)
    write_bin_boundaries_yaml(simple_boundaries, "bin_boundaries.yaml")

    hist = build_nd_histogram(counts, simple_boundaries)
    write_histogram_pickle(hist, "histogram.pkl")

    top = top_bins(hist, n=10)
    bottom = bottom_bins(hist, n=10)
    print_bin_table(top, "Top 10 bins")
    print_bin_table(bottom, "Least 10 bins")


if __name__ == "__main__":
    app()
