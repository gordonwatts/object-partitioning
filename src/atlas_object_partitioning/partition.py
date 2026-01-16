from typing import Dict, List, Optional, Tuple
import numpy as np
import awkward as ak
import typer
import yaml
from hist import BaseHist
from rich.console import Console
from rich.table import Table

from atlas_object_partitioning.histograms import (
    apply_tail_caps,
    bottom_bins,
    build_nd_histogram,
    compute_bin_boundaries,
    histogram_summary,
    histogram_boundaries,
    MergedCellGroup,
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


def _load_bin_boundaries_file(
    file_path: str,
) -> Tuple[Dict[str, List[int]], Optional[MergedCells]]:
    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as exc:
        raise typer.BadParameter(f"{file_path} does not exist.") from exc
    if not isinstance(data, dict) or "axes" not in data:
        raise typer.BadParameter(f"{file_path} does not contain axes data.")
    axes = data["axes"]
    if not isinstance(axes, dict) or not axes:
        raise typer.BadParameter(f"{file_path} axes entry is not a mapping.")
    cleaned_axes: Dict[str, List[int]] = {}
    for axis, edges in axes.items():
        if not isinstance(axis, str) or not axis:
            raise typer.BadParameter(f"{file_path} has an invalid axis name.")
        if not isinstance(edges, list):
            raise typer.BadParameter(f"{file_path} axis {axis} edges are not a list.")
        if len(edges) < 2:
            raise typer.BadParameter(
                f"{file_path} axis {axis} needs at least two bin edges."
            )
        try:
            cleaned_axes[axis] = [int(edge) for edge in edges]
        except (TypeError, ValueError) as exc:
            raise typer.BadParameter(
                f"{file_path} axis {axis} edges must be integers."
            ) from exc
    merged_cells_data = data.get("merged_cells")
    if merged_cells_data is None:
        return cleaned_axes, None
    if not isinstance(merged_cells_data, dict):
        raise typer.BadParameter(f"{file_path} merged_cells entry is not a mapping.")
    if "groups" not in merged_cells_data:
        raise typer.BadParameter(f"{file_path} merged_cells is missing groups.")
    try:
        min_fraction = float(merged_cells_data.get("min_fraction", 0.0))
    except (TypeError, ValueError) as exc:
        raise typer.BadParameter(
            f"{file_path} merged_cells.min_fraction must be numeric."
        ) from exc
    groups = merged_cells_data["groups"]
    if not isinstance(groups, list):
        raise typer.BadParameter(f"{file_path} merged_cells.groups must be a list.")
    cleaned_groups: List[List[Dict[str, int]]] = []
    for group in groups:
        if not isinstance(group, dict) or "cells" not in group:
            raise typer.BadParameter(
                f"{file_path} merged_cells.groups entries must be mappings with cells."
            )
        cells = group["cells"]
        if not isinstance(cells, list):
            raise typer.BadParameter(
                f"{file_path} merged_cells group cells must be a list."
            )
        cleaned_cells: List[Dict[str, int]] = []
        for cell in cells:
            if not isinstance(cell, dict):
                raise typer.BadParameter(
                    f"{file_path} merged_cells cell entries must be mappings."
                )
            cleaned_cell: Dict[str, int] = {}
            for axis, value in cell.items():
                if not isinstance(axis, str) or not axis:
                    raise typer.BadParameter(
                        f"{file_path} merged_cells cell axis names must be strings."
                    )
                try:
                    cleaned_cell[axis] = int(value)
                except (TypeError, ValueError) as exc:
                    raise typer.BadParameter(
                        f"{file_path} merged_cells cell values must be integers."
                    ) from exc
            cleaned_cells.append(cleaned_cell)
        cleaned_groups.append(cleaned_cells)
    merged_cells = MergedCells(
        min_fraction=min_fraction,
        groups=[
            MergedCellGroup(cells=group, count=0, fraction=0.0)
            for group in cleaned_groups
        ],
    )
    return cleaned_axes, merged_cells


def _format_index_ranges(indices: List[int]) -> str:
    if not indices:
        return "-"
    ranges: List[Tuple[int, int]] = []
    start = indices[0]
    end = indices[0]
    for value in indices[1:]:
        if value == end + 1:
            end = value
        else:
            ranges.append((start, end))
            start = value
            end = value
    ranges.append((start, end))
    parts = []
    for lo, hi in ranges:
        if lo == hi:
            parts.append(str(lo))
        else:
            parts.append(f"{lo}-{hi}")
    return ", ".join(parts)


def _format_index_ranges_with_edges(indices: List[int], edges: List[int]) -> str:
    if not indices:
        return "-"
    ranges: List[Tuple[int, int]] = []
    start = indices[0]
    end = indices[0]
    for value in indices[1:]:
        if value == end + 1:
            end = value
        else:
            ranges.append((start, end))
            start = value
            end = value
    ranges.append((start, end))
    parts = []
    for lo, hi in ranges:
        lo_edge = edges[lo]
        hi_edge = edges[hi + 1]
        if lo == hi:
            parts.append(f"{lo} [{lo_edge}, {hi_edge})")
        else:
            parts.append(f"{lo}-{hi} [{lo_edge}, {hi_edge})")
    return ", ".join(parts)


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


@app.command("partition")
def partition(
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


@app.command("repartition")
def repartition(
    ds_name: str = typer.Argument(..., help="Name of the dataset"),
    bin_boundaries_file: str = typer.Argument(
        ..., help="Path to the existing bin_boundaries.yaml file."
    ),
    output_file: str = typer.Option(
        "bin_boundaries.repartition.yaml",
        "--output",
        "-o",
        help="Output file name for the updated bin_boundaries.yaml file.",
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
):
    """Update merged cell counts using an existing bin_boundaries.yaml."""
    if output_file == bin_boundaries_file:
        raise typer.BadParameter(
            "--output must be different from the input bin_boundaries.yaml file."
        )

    boundaries, merged_cells = _load_bin_boundaries_file(bin_boundaries_file)
    if merged_cells is None:
        raise typer.BadParameter(
            f"{bin_boundaries_file} does not contain merged cell groups to update."
        )

    counts = collect_object_counts(
        ds_name,
        n_files=n_files,
        servicex_name=servicex_name,
        ignore_local_cache=ignore_cache,
    )
    missing_axes = [ax for ax in boundaries if ax not in counts.fields]
    if missing_axes:
        raise typer.BadParameter(
            "Input bin_boundaries.yaml references missing axes: "
            f"{', '.join(missing_axes)}"
        )

    hist = build_nd_histogram(counts, boundaries)
    summary = histogram_summary(hist)

    counts_view = np.asarray(hist.view())
    total = int(counts_view.sum())
    axes_order = list(boundaries.keys())
    merged_groups: List[MergedCellGroup] = []
    for group in merged_cells.groups:
        group_total = 0
        for cell in group.cells:
            if any(axis not in cell for axis in axes_order):
                raise typer.BadParameter(
                    f"{bin_boundaries_file} has cells missing axes in a group."
                )
            idx = tuple(int(cell[axis]) for axis in axes_order)
            if any(
                idx[i] < 0 or idx[i] >= counts_view.shape[i]
                for i in range(len(idx))
            ):
                raise typer.BadParameter(
                    f"{bin_boundaries_file} has out-of-range cell indices."
                )
            group_total += int(counts_view[idx])
        fraction = 0.0 if total == 0 else float(group_total) / float(total)
        merged_groups.append(
            MergedCellGroup(cells=group.cells, count=group_total, fraction=fraction)
        )
    merged_cells = MergedCells(
        min_fraction=merged_cells.min_fraction,
        groups=merged_groups,
    )

    write_bin_boundaries_yaml(
        boundaries,
        output_file,
        merged_cells=merged_cells,
    )
    typer.echo(
        "Histogram summary: max fraction "
        f"{summary['max_fraction']:.3f}, min fraction "
        f"{summary['min_fraction']:.3f}, min nonzero fraction "
        f"{summary['min_nonzero_fraction']:.3f}, zero bins "
        f"{summary['zero_bins']:,}"
    )


@app.command("describe-cells")
def describe_cells(
    file_path: str = typer.Argument(
        "bin_boundaries.yaml",
        help="Path to the bin_boundaries.yaml file.",
    ),
    show_values: bool = typer.Option(
        False,
        "--show-values",
        help="Include bin edge ranges alongside index ranges.",
    ),
    sort_by_size: bool = typer.Option(
        False,
        "--sort-by-size/--no-sort-by-size",
        help="Sort groups by size (count) descending.",
    ),
) -> None:
    """Pretty-print merged n-D cell groups from bin_boundaries.yaml."""
    with open(file_path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "axes" not in data:
        raise typer.BadParameter(f"{file_path} does not contain axes data.")
    axes = data["axes"]
    if not isinstance(axes, dict):
        raise typer.BadParameter(f"{file_path} axes entry is not a mapping.")
    merged = data.get("merged_cells")
    if not merged or not merged.get("groups"):
        typer.echo("No merged cell groups found.")
        return

    groups = merged["groups"]
    if sort_by_size:
        groups = sorted(
            groups,
            key=lambda group: (
                -int(group.get("count", 0)),
                -float(group.get("fraction", 0.0)),
            ),
        )
    axes_order = list(axes.keys())
    table = Table(title=f"Merged cell groups ({len(groups):,})")
    table.add_column("group", justify="right")
    table.add_column("count", justify="right")
    table.add_column("fraction", justify="right")
    for axis in axes_order:
        table.add_column(axis)
    for idx, group in enumerate(groups, start=1):
        cells = group.get("cells", [])
        count = int(group.get("count", 0))
        fraction = float(group.get("fraction", 0.0))
        axis_indices: Dict[str, List[int]] = {axis: [] for axis in axes_order}
        for cell in cells:
            for axis in axes_order:
                if axis in cell:
                    axis_indices[axis].append(int(cell[axis]))
        axis_parts = []
        for axis in axes_order:
            values = sorted(set(axis_indices[axis]))
            if show_values:
                axis_parts.append(
                    _format_index_ranges_with_edges(values, axes[axis])
                )
            else:
                axis_parts.append(_format_index_ranges(values))
        table.add_row(
            str(idx),
            f"{count:,}",
            f"{fraction:.3f}",
            *axis_parts,
        )
    Console().print(table)


if __name__ == "__main__":
    app()
