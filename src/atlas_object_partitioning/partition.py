from typing import Dict, List, Optional, Tuple
import numpy as np
import awkward as ak
import typer
from hist import BaseHist

from atlas_object_partitioning.histograms import (
    apply_tail_caps,
    bottom_bins,
    build_nd_histogram,
    compute_bin_boundaries,
    histogram_summary,
    histogram_boundaries,
    MergedCells,
    merge_sparse_bins,
    merge_sparse_cells,
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


def _adaptive_score(
    summary: Dict[str, float],
    target_min_fraction: float,
    target_max_fraction: float,
) -> Tuple[float, float, int, float, float]:
    max_over = max(0.0, summary["max_fraction"] - target_max_fraction)
    min_under = max(0.0, target_min_fraction - summary["min_nonzero_fraction"])
    return (
        max_over,
        min_under,
        int(summary["zero_bins"]),
        -summary["min_nonzero_fraction"],
        summary["max_fraction"],
    )


def _adaptive_bins_search(
    counts: ak.Array,
    ignore_axes: List[str],
    bins_per_axis: int,
    overrides: Dict[str, int],
    target_min_fraction: float,
    target_max_fraction: float,
    min_bins: int,
) -> Tuple[Dict[str, int], Dict[str, List[int]], BaseHist, Dict[str, float]]:
    axes = [ax for ax in counts.fields if ax not in ignore_axes]
    bins_by_axis = {ax: overrides.get(ax, bins_per_axis) for ax in axes}
    fixed_axes = set(overrides.keys())

    def build_from_bins(
        candidate_bins: Dict[str, int],
    ) -> Tuple[Dict[str, List[int]], BaseHist, Dict[str, float]]:
        boundaries = compute_bin_boundaries(
            counts,
            ignore_axes=ignore_axes,
            bins_per_axis=1,
            bins_per_axis_overrides=candidate_bins,
        )
        hist = build_nd_histogram(counts, boundaries)
        summary = histogram_summary(hist)
        return boundaries, hist, summary

    boundaries, hist, summary = build_from_bins(bins_by_axis)
    current_score = _adaptive_score(
        summary, target_min_fraction, target_max_fraction
    )
    max_steps = sum(
        max(0, bins_by_axis[ax] - min_bins)
        for ax in axes
        if ax not in fixed_axes
    )
    for _ in range(max_steps):
        if (
            summary["max_fraction"] <= target_max_fraction
            and summary["min_nonzero_fraction"] >= target_min_fraction
        ):
            break
        best = None
        best_score = None
        for axis in axes:
            if axis in fixed_axes or bins_by_axis[axis] <= min_bins:
                continue
            candidate_bins = dict(bins_by_axis)
            candidate_bins[axis] -= 1
            candidate_boundaries, candidate_hist, candidate_summary = build_from_bins(
                candidate_bins
            )
            score = _adaptive_score(
                candidate_summary, target_min_fraction, target_max_fraction
            )
            if best is None or score < best_score:
                best = (
                    axis,
                    candidate_bins,
                    candidate_boundaries,
                    candidate_hist,
                    candidate_summary,
                )
                best_score = score

        if best is None or best_score is None or best_score >= current_score:
            break
        axis, bins_by_axis, boundaries, hist, summary = best
        current_score = best_score
        typer.echo(
            "  adaptive reduce "
            f"{axis}={bins_by_axis[axis]}: "
            f"max {summary['max_fraction']:.3f}, "
            f"min nonzero {summary['min_nonzero_fraction']:.3f}, "
            f"zero bins {summary['zero_bins']:,}"
        )

    return bins_by_axis, boundaries, hist, summary


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
    adaptive_bins: bool = typer.Option(
        False,
        "--adaptive-bins",
        help="Adaptively reduce bins per axis to approach target min/max fractions.",
    ),
    adaptive_min_fraction: float = typer.Option(
        0.01,
        "--adaptive-min-fraction",
        help="Target minimum nonzero bin fraction for adaptive binning.",
    ),
    adaptive_max_fraction: float = typer.Option(
        0.05,
        "--adaptive-max-fraction",
        help="Target maximum bin fraction for adaptive binning.",
    ),
    adaptive_min_bins: int = typer.Option(
        1,
        "--adaptive-min-bins",
        help="Minimum bins allowed per axis when adaptively reducing bins.",
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
    tail_cap_quantile: Optional[float] = typer.Option(
        None,
        "--tail-cap-quantile",
        help="Cap per-axis counts at this quantile (0-1] before binning.",
    ),
    merge_min_fraction: Optional[float] = typer.Option(
        None,
        "--merge-min-fraction",
        help="Minimum marginal bin fraction per axis; bins below are merged with neighbors.",
    ),
    merge_min_bins: int = typer.Option(
        1,
        "--merge-min-bins",
        help="Minimum bins allowed per axis when merging sparse bins.",
    ),
    merge_cell_min_fraction: Optional[float] = typer.Option(
        None,
        "--merge-cell-min-fraction",
        help="Minimum fraction for merged n-D grid cells; sparse adjacent cells are grouped.",
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
    if adaptive_bins and use_target_scan:
        raise typer.BadParameter(
            "--adaptive-bins cannot be combined with --target-min-fraction/--target-max-fraction."
        )
    if adaptive_min_bins < 1:
        raise typer.BadParameter("--adaptive-min-bins must be >= 1.")
    if not 0.0 <= adaptive_min_fraction <= 1.0:
        raise typer.BadParameter("--adaptive-min-fraction must be between 0 and 1.")
    if not 0.0 <= adaptive_max_fraction <= 1.0:
        raise typer.BadParameter("--adaptive-max-fraction must be between 0 and 1.")
    if target_min_fraction is not None and not 0.0 <= target_min_fraction <= 1.0:
        raise typer.BadParameter("--target-min-fraction must be between 0 and 1.")
    if target_max_fraction is not None and not 0.0 <= target_max_fraction <= 1.0:
        raise typer.BadParameter("--target-max-fraction must be between 0 and 1.")
    if tail_cap_quantile is not None and not 0.0 < tail_cap_quantile <= 1.0:
        raise typer.BadParameter("--tail-cap-quantile must be between 0 and 1.")
    if target_bins_min < 1:
        raise typer.BadParameter("--target-bins-min must be >= 1.")
    if target_bins_max < target_bins_min:
        raise typer.BadParameter("--target-bins-max must be >= --target-bins-min.")
    if merge_min_fraction is not None and not 0.0 <= merge_min_fraction <= 1.0:
        raise typer.BadParameter("--merge-min-fraction must be between 0 and 1.")
    if merge_min_bins < 1:
        raise typer.BadParameter("--merge-min-bins must be >= 1.")
    if merge_cell_min_fraction is not None and not 0.0 <= merge_cell_min_fraction <= 1.0:
        raise typer.BadParameter("--merge-cell-min-fraction must be between 0 and 1.")

    counts_for_bins = counts
    tail_caps: Dict[str, int] = {}
    if tail_cap_quantile is not None and tail_cap_quantile < 1.0:
        counts_for_bins, tail_caps = apply_tail_caps(
            counts,
            ignore_axes=ignore_axes,
            tail_cap_quantile=tail_cap_quantile,
        )
        if tail_caps:
            caps_summary = ", ".join(
                f"{axis}={tail_caps[axis]}" for axis in sorted(tail_caps)
            )
            typer.echo(
                f"Applied tail caps (q={tail_cap_quantile:.3f}): {caps_summary}"
            )
        else:
            typer.echo(
                f"Tail cap quantile {tail_cap_quantile:.3f} had no effect on axes."
            )

    if use_target_scan:
        typer.echo(
            "Scanning bins-per-axis "
            f"{target_bins_min}-{target_bins_max} for target fractions."
        )
        best = None
        best_score = None
        for candidate in range(target_bins_min, target_bins_max + 1):
            candidate_boundaries = compute_bin_boundaries(
                counts_for_bins,
                ignore_axes=ignore_axes,
                bins_per_axis=candidate,
                bins_per_axis_overrides=overrides,
            )
            candidate_hist = build_nd_histogram(counts_for_bins, candidate_boundaries)
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
        if adaptive_bins:
            typer.echo(
                "Running adaptive bin reduction with targets: "
                f"min nonzero {adaptive_min_fraction:.3f}, "
                f"max {adaptive_max_fraction:.3f}."
            )
            bins_by_axis, simple_boundaries, hist, summary = _adaptive_bins_search(
                counts_for_bins,
                ignore_axes=ignore_axes,
                bins_per_axis=bins_per_axis,
                overrides=overrides,
                target_min_fraction=adaptive_min_fraction,
                target_max_fraction=adaptive_max_fraction,
                min_bins=adaptive_min_bins,
            )
            typer.echo(
                "Adaptive binning result: "
                + ", ".join(f"{ax}={bins_by_axis[ax]}" for ax in sorted(bins_by_axis))
            )
        else:
            simple_boundaries = compute_bin_boundaries(
                counts_for_bins,
                ignore_axes=ignore_axes,
                bins_per_axis=bins_per_axis,
                bins_per_axis_overrides=overrides,
            )
            hist = build_nd_histogram(counts_for_bins, simple_boundaries)
            summary = histogram_summary(hist)

    if merge_min_fraction is not None:
        hist, merges = merge_sparse_bins(
            hist,
            min_fraction=merge_min_fraction,
            min_bins=merge_min_bins,
        )
        simple_boundaries = histogram_boundaries(hist)
        merge_summary = ", ".join(
            f"{axis}={merges[axis]}" for axis in sorted(merges)
        )
        typer.echo(
            "Merged sparse bins (min fraction "
            f"{merge_min_fraction:.3f}, min bins {merge_min_bins}): {merge_summary}"
        )
        summary = histogram_summary(hist)

    merged_cells: Optional[MergedCells] = None
    merged_summary: Optional[Dict[str, float]] = None
    if merge_cell_min_fraction is not None:
        total_cells = int(np.asarray(hist.view()).size)
        merged_groups, merged_summary = merge_sparse_cells(
            hist,
            min_fraction=merge_cell_min_fraction,
        )
        combined_cells = total_cells - len(merged_groups)
        merged_cells = MergedCells(
            min_fraction=merge_cell_min_fraction,
            groups=merged_groups,
        )
        typer.echo(
            "Merged cell summary: "
            f"total cells {total_cells:,}, combined {combined_cells:,}, "
            f"groups {len(merged_groups):,}, "
            f"max fraction {merged_summary['max_fraction']:.3f}, "
            f"min fraction {merged_summary['min_fraction']:.3f}, "
            f"min nonzero fraction {merged_summary['min_nonzero_fraction']:.3f}, "
            f"zero groups {merged_summary['zero_bins']:,}"
        )

    write_bin_boundaries_yaml(
        simple_boundaries,
        "bin_boundaries.yaml",
        merged_cells=merged_cells,
    )
    write_histogram_pickle(hist, "histogram.pkl")

    top = top_bins(hist, n=10)
    bottom = bottom_bins(hist, n=10)
    print_bin_table(top, "Top 10 bins")
    print_bin_table(bottom, "Least 10 bins")
    if use_target_scan or adaptive_bins:
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
