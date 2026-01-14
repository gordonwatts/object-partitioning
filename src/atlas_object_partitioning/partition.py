from typing import Dict, List
import awkward as ak
import typer

from atlas_object_partitioning.histograms import (
    bottom_bins,
    build_nd_histogram,
    compute_bin_boundaries,
    histogram_summary,
    print_bin_table,
    top_bins,
    write_bin_boundaries_yaml,
    write_histogram_pickle,
)
from atlas_object_partitioning.scan_ds import collect_object_counts

app = typer.Typer()


def _parse_bins_per_axis_overrides(entries: List[str]) -> Dict[str, int]:
    overrides: Dict[str, int] = {}
    for entry in entries:
        if "=" not in entry:
            raise typer.BadParameter(
                f"Invalid --bins-per-axis-override value '{entry}'. Expected AXIS=INT."
            )
        axis, value = entry.split("=", 1)
        if not axis:
            raise typer.BadParameter(
                f"Invalid --bins-per-axis-override value '{entry}'. Axis cannot be empty."
            )
        try:
            bins = int(value)
        except ValueError as exc:
            raise typer.BadParameter(
                f"Invalid --bins-per-axis-override value '{entry}'. "
                "Bins must be an integer."
            ) from exc
        if bins < 1:
            raise typer.BadParameter(
                f"Invalid --bins-per-axis-override value '{entry}'. "
                "Bins must be >= 1."
            )
        if axis in overrides:
            raise typer.BadParameter(
                f"Duplicate --bins-per-axis-override axis '{axis}'."
            )
        overrides[axis] = bins
    return overrides


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
    bins_per_axis: int = typer.Option(
        4,
        "--bins-per-axis",
        help="Number of bins to use per axis when computing boundaries.",
    ),
    bins_per_axis_override: List[str] = typer.Option(
        [],
        "--bins-per-axis-override",
        help="Override bins per axis, format AXIS=INT (repeat for multiple axes).",
    ),
):
    """Use counts of PHYSLITE objects in a rucio dataset to determine skim binning.

    - Each *axis* is a count of PHYSLITE objects (muons, electrons, jets, etc).

    - Looks at each axis and tries to divide the counts into equal bins of events.

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

    overrides = _parse_bins_per_axis_overrides(bins_per_axis_override)
    simple_boundaries = compute_bin_boundaries(
        counts,
        ignore_axes=ignore_axes,
        bins_per_axis=bins_per_axis,
        bins_per_axis_overrides=overrides,
    )
    write_bin_boundaries_yaml(simple_boundaries, "bin_boundaries.yaml")

    hist = build_nd_histogram(counts, simple_boundaries)
    write_histogram_pickle(hist, "histogram.pkl")

    top = top_bins(hist, n=10)
    bottom = bottom_bins(hist, n=10)
    print_bin_table(top, "Top 10 bins")
    print_bin_table(bottom, "Least 10 bins")
    summary = histogram_summary(hist)
    typer.echo(
        f"Histogram summary: max fraction {summary['max_fraction']:.3f}, "
        f"zero bins {summary['zero_bins']:,}"
    )


if __name__ == "__main__":
    app()
