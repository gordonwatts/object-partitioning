from typing import Dict, List, Optional, Tuple
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


def _score_candidate(
    summary: Dict[str, float],
    target_min_fraction: Optional[float],
    target_max_fraction: Optional[float],
) -> Tuple[bool, bool, float, float, float]:
    max_over = 0.0
    if target_max_fraction is not None:
        max_over = max(0.0, summary["max_fraction"] - target_max_fraction)
    min_under = 0.0
    if target_min_fraction is not None:
        min_under = max(0.0, target_min_fraction - summary["min_fraction"])
    return (
        max_over > 0.0,
        min_under > 0.0,
        max_over + min_under,
        summary["max_fraction"],
        -summary["min_fraction"],
    )


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
    target_min_fraction: Optional[float] = typer.Option(
        None,
        "--target-min-fraction",
        help="Target minimum bin fraction when scanning bins-per-axis.",
    ),
    target_max_fraction: Optional[float] = typer.Option(
        None,
        "--target-max-fraction",
        help="Target maximum bin fraction when scanning bins-per-axis.",
    ),
    target_bins_min: int = typer.Option(
        1,
        "--target-bins-min",
        help="Minimum bins-per-axis to scan when targeting bin fractions.",
    ),
    target_bins_max: int = typer.Option(
        6,
        "--target-bins-max",
        help="Maximum bins-per-axis to scan when targeting bin fractions.",
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
    use_target_scan = target_min_fraction is not None or target_max_fraction is not None
    if target_min_fraction is not None and not 0.0 <= target_min_fraction <= 1.0:
        raise typer.BadParameter("--target-min-fraction must be between 0 and 1.")
    if target_max_fraction is not None and not 0.0 <= target_max_fraction <= 1.0:
        raise typer.BadParameter("--target-max-fraction must be between 0 and 1.")
    if target_bins_min < 1:
        raise typer.BadParameter("--target-bins-min must be >= 1.")
    if target_bins_max < target_bins_min:
        raise typer.BadParameter("--target-bins-max must be >= --target-bins-min.")

    if use_target_scan:
        typer.echo(
            "Scanning bins-per-axis "
            f"{target_bins_min}-{target_bins_max} for target fractions."
        )
        best = None
        best_score = None
        for candidate in range(target_bins_min, target_bins_max + 1):
            candidate_boundaries = compute_bin_boundaries(
                counts,
                ignore_axes=ignore_axes,
                bins_per_axis=candidate,
                bins_per_axis_overrides=overrides,
            )
            candidate_hist = build_nd_histogram(counts, candidate_boundaries)
            candidate_summary = histogram_summary(candidate_hist)
            typer.echo(
                "  bins-per-axis "
                f"{candidate}: max {candidate_summary['max_fraction']:.3f}, "
                f"min {candidate_summary['min_fraction']:.3f}, "
                f"zero bins {candidate_summary['zero_bins']:,}"
            )
            score = _score_candidate(
                candidate_summary, target_min_fraction, target_max_fraction
            )
            if best is None or score < best_score:
                best = (candidate, candidate_boundaries, candidate_hist, candidate_summary)
                best_score = score

        assert best is not None
        bins_per_axis, simple_boundaries, hist, summary = best
        max_ok = (
            target_max_fraction is None
            or summary["max_fraction"] <= target_max_fraction
        )
        min_ok = (
            target_min_fraction is None
            or summary["min_fraction"] >= target_min_fraction
        )
        if max_ok and min_ok:
            typer.echo(
                f"Selected bins-per-axis {bins_per_axis} meeting target fractions."
            )
        else:
            typer.echo(
                "No bins-per-axis met targets; "
                f"selected {bins_per_axis} with smallest deviation."
            )
    else:
        simple_boundaries = compute_bin_boundaries(
            counts,
            ignore_axes=ignore_axes,
            bins_per_axis=bins_per_axis,
            bins_per_axis_overrides=overrides,
        )
        hist = build_nd_histogram(counts, simple_boundaries)
        summary = histogram_summary(hist)

    write_bin_boundaries_yaml(simple_boundaries, "bin_boundaries.yaml")
    write_histogram_pickle(hist, "histogram.pkl")

    top = top_bins(hist, n=10)
    bottom = bottom_bins(hist, n=10)
    print_bin_table(top, "Top 10 bins")
    print_bin_table(bottom, "Least 10 bins")
    if use_target_scan:
        typer.echo(
            "Histogram summary: max fraction "
            f"{summary['max_fraction']:.3f}, min fraction "
            f"{summary['min_fraction']:.3f}, min nonzero fraction "
            f"{summary['min_nonzero_fraction']:.3f}, zero bins "
            f"{summary['zero_bins']:,}"
        )
    else:
        typer.echo(
            f"Histogram summary: max fraction {summary['max_fraction']:.3f}, "
            f"zero bins {summary['zero_bins']:,}"
        )


if __name__ == "__main__":
    app()
