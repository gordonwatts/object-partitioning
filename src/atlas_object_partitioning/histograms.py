import pickle
from typing import Dict, List, Optional, Tuple

import awkward as ak
import numpy as np
import yaml
from hist import BaseHist, Hist
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table


def _compute_boundaries(values: ak.Array, n_bins: int) -> List[int]:
    """Compute boundary values that split the distribution into ``n_bins`` bins.

    Parameters
    ----------
    values: ak.Array
        Array of values for a single axis.
    Returns
    -------
    List[int]
        List of boundary values (upper edge of each quantile).
    """
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")
    if len(values) == 0:
        return []
    min_val = int(ak.min(values))
    max_val = int(ak.max(values))
    bins = np.arange(min_val, max_val + 2)
    hist, edges = np.histogram(values, bins=bins)
    cdf = np.cumsum(hist)
    step = cdf[-1] / n_bins
    boundaries: List[int] = []
    for i in range(1, n_bins):
        idx = int(np.searchsorted(cdf, step * i))
        boundaries.append(int(edges[idx + 1]))

    # Always return [min, ...boundaries..., max+1]
    boundaries = [min_val] + boundaries + [max_val + 1]

    # Make sure all boundaries entries are unique
    boundaries = sorted(set(boundaries))

    return boundaries


def compute_bin_boundaries(
    data: ak.Array,
    ignore_axes: Optional[List[str]] = None,
    bins_per_axis: int = 4,
    bins_per_axis_overrides: Optional[Dict[str, int]] = None,
) -> Dict[str, List[int]]:
    """Compute bin boundaries for all axes in the awkward array."""
    if ignore_axes is None:
        ignore_axes = []
    if bins_per_axis_overrides is None:
        bins_per_axis_overrides = {}
    missing = [ax for ax in ignore_axes if ax not in data.fields]
    if len(missing) > 0:
        raise ValueError(f"Cannot ignore missing axes: {', '.join(missing)}")
    override_missing = [
        ax for ax in bins_per_axis_overrides.keys() if ax not in data.fields
    ]
    if len(override_missing) > 0:
        raise ValueError(
            "Cannot override bins for missing axes: "
            f"{', '.join(override_missing)}"
        )
    override_ignored = [ax for ax in bins_per_axis_overrides.keys() if ax in ignore_axes]
    if len(override_ignored) > 0:
        raise ValueError(
            "Cannot override bins for ignored axes: " f"{', '.join(override_ignored)}"
        )

    result: Dict[str, List[int]] = {}
    good_data_fields = [ax for ax in data.fields if ax not in ignore_axes]
    for axis in good_data_fields:
        axis_bins = bins_per_axis_overrides.get(axis, bins_per_axis)
        result[axis] = _compute_boundaries(data[axis], axis_bins)
    return result


def apply_tail_caps(
    data: ak.Array,
    ignore_axes: Optional[List[str]] = None,
    tail_cap_quantile: Optional[float] = None,
) -> Tuple[ak.Array, Dict[str, int]]:
    """Cap per-axis counts at a quantile to reduce long tails."""
    if ignore_axes is None:
        ignore_axes = []
    if tail_cap_quantile is None or tail_cap_quantile >= 1.0:
        return data, {}
    if not 0.0 < tail_cap_quantile <= 1.0:
        raise ValueError("tail_cap_quantile must be between 0 and 1.")

    capped: Dict[str, ak.Array] = {}
    caps: Dict[str, int] = {}
    for axis in data.fields:
        values = data[axis]
        if axis in ignore_axes or len(values) == 0:
            capped[axis] = values
            continue
        values_np = ak.to_numpy(values)
        cap_value = int(np.quantile(values_np, tail_cap_quantile))
        max_value = int(values_np.max())
        if cap_value < max_value:
            caps[axis] = cap_value
            capped[axis] = ak.where(values > cap_value, cap_value, values)
        else:
            capped[axis] = values
    return ak.zip(capped, depth_limit=1), caps


class MergedCellGroup(BaseModel):
    cells: List[Dict[str, int]]
    count: int
    fraction: float


class MergedCells(BaseModel):
    min_fraction: float
    groups: List[MergedCellGroup]


class BinBoundaries(BaseModel):
    axes: Dict[str, List[int]]
    merged_cells: Optional[MergedCells] = None


def write_bin_boundaries_yaml(
    boundaries: Dict[str, List[int]],
    file_path: str,
    merged_cells: Optional[MergedCells] = None,
) -> None:
    """Write the bin boundaries to ``file_path`` in YAML format."""
    data = BinBoundaries(axes=boundaries, merged_cells=merged_cells)
    with open(file_path, "w") as f:
        yaml.safe_dump(data.model_dump(), f)


def build_nd_histogram(data: ak.Array, boundaries: Dict[str, List[int]]) -> BaseHist:
    """Build an n-dimensional histogram using ``boundaries`` and return a
    :class:`hist.Hist` object.

    Parameters
    ----------
    data:
        Event-by-event counts of objects.
    boundaries:
        Mapping from axis name to bin boundaries.

    Returns
    -------
    ``hist.Hist`` instance populated with the supplied data.
    """
    axes = list(boundaries.keys())

    # Build the histogram using ``hist`` which leverages boost-histogram
    h_builder = Hist.new
    for ax in axes:
        h_builder = h_builder.Var(boundaries[ax], name=ax, label=ax)
    h_builder = h_builder.Int64()  # type: ignore
    h = h_builder  # type: BaseHist

    # Fill with event counts
    fill_dict = {ax: ak.to_numpy(data[ax]) for ax in axes}
    h.fill(**fill_dict)

    return h


def histogram_boundaries(hist: BaseHist) -> Dict[str, List[int]]:
    """Extract axis boundaries from a histogram."""
    boundaries: Dict[str, List[int]] = {}
    for ax in hist.axes:
        name = ax.name if ax.name is not None else ""
        edges = np.asarray(ax.edges)
        boundaries[name] = [int(edge) for edge in edges.tolist()]
    return boundaries


def _merge_group_sizes(
    counts: np.ndarray,
    min_fraction: float,
    min_bins: int,
) -> List[int]:
    total = int(counts.sum())
    n_bins = int(counts.size)
    if total == 0 or n_bins <= min_bins or min_fraction <= 0.0:
        return [1] * n_bins

    group_sizes = [1] * n_bins
    counts_list = counts.astype(int).tolist()
    while len(counts_list) > min_bins:
        fractions = [c / total for c in counts_list]
        if min(fractions) >= min_fraction:
            break
        idx = int(np.argmin(counts_list))
        if len(counts_list) == 1:
            break
        if idx == 0:
            neighbor = 1
        elif idx == len(counts_list) - 1:
            neighbor = idx - 1
        else:
            neighbor = idx - 1 if counts_list[idx - 1] <= counts_list[idx + 1] else idx + 1
        if neighbor < idx:
            counts_list[neighbor] += counts_list[idx]
            group_sizes[neighbor] += group_sizes[idx]
            del counts_list[idx]
            del group_sizes[idx]
        else:
            counts_list[idx] += counts_list[neighbor]
            group_sizes[idx] += group_sizes[neighbor]
            del counts_list[neighbor]
            del group_sizes[neighbor]
    return group_sizes


def merge_sparse_bins(
    hist: BaseHist,
    min_fraction: float,
    min_bins: int = 1,
) -> Tuple[BaseHist, Dict[str, int]]:
    """Merge adjacent bins with low marginal fractions along each axis."""
    if not 0.0 <= min_fraction <= 1.0:
        raise ValueError("min_fraction must be between 0 and 1.")
    if min_bins < 1:
        raise ValueError("min_bins must be >= 1.")

    counts = np.asarray(hist.view())
    axes = list(hist.axes)
    merges: Dict[str, int] = {}
    edges_by_axis = [np.asarray(ax.edges) for ax in axes]

    for axis_idx, axis in enumerate(axes):
        if counts.size == 0:
            merges[axis.name or f"axis_{axis_idx}"] = 0
            continue
        axis_counts = counts.sum(
            axis=tuple(i for i in range(counts.ndim) if i != axis_idx)
        )
        group_sizes = _merge_group_sizes(axis_counts, min_fraction, min_bins)
        if len(group_sizes) == counts.shape[axis_idx]:
            merges[axis.name or f"axis_{axis_idx}"] = 0
            continue
        merges[axis.name or f"axis_{axis_idx}"] = (
            counts.shape[axis_idx] - len(group_sizes)
        )
        starts = np.cumsum([0] + group_sizes[:-1])
        counts = np.add.reduceat(counts, starts, axis=axis_idx)
        cumulative = np.cumsum(group_sizes)
        new_edges = [edges_by_axis[axis_idx][0]]
        new_edges.extend(edges_by_axis[axis_idx][cumulative].tolist())
        edges_by_axis[axis_idx] = np.asarray(new_edges)

    h_builder = Hist.new
    for axis, edges in zip(axes, edges_by_axis):
        name = axis.name if axis.name is not None else ""
        label = axis.label if axis.label is not None else name
        h_builder = h_builder.Var(edges.tolist(), name=name, label=label)
    h_builder = h_builder.Int64()  # type: ignore
    merged_hist = h_builder
    merged_hist[...] = counts
    return merged_hist, merges

def write_histogram_pickle(hist: BaseHist, file_path: str) -> None:
    """Persist the histogram to disk using :mod:`pickle`.
    This currently is the most efficient way to store the histogram
    according to the histogram authors. A new serialization method that
    should be cross-program (e.g. ROOT should be able to read it) is
    coming.
    """
    with open(file_path, "wb") as f:
        pickle.dump(hist, f)


def load_histogram_pickle(file_path: str) -> Hist:
    """Load a histogram previously written with :func:`write_histogram_pickle`."""
    with open(file_path, "rb") as f:
        hist = pickle.load(f)
    return hist


def _sorted_bin_records(
    hist: BaseHist,
    n: int,
    ascending: bool = False,
) -> List[Dict[str, object]]:
    counts = np.asarray(hist.view())
    flat = counts.flatten()
    total = int(flat.sum())
    order = np.argsort(flat)
    if not ascending:
        order = order[::-1]
    records = []
    edges = [np.asarray(ax.edges) for ax in hist.axes]
    axes_names = [
        ax.name if ax.name is not None else f"axis_{i}" for i, ax in enumerate(hist.axes)
    ]
    for idx in order[:n]:
        count = int(flat[idx])
        frac = 0.0 if total == 0 else float(count) / float(total)
        bin_idx = np.unravel_index(idx, counts.shape)
        label = {
            name: (edges[i][b], edges[i][b + 1])
            for i, (name, b) in enumerate(zip(axes_names, bin_idx))
        }
        records.append({"bin": label, "count": count, "fraction": frac})
    return records


def top_bins(hist: BaseHist, n: int = 10) -> List[Dict[str, object]]:
    """Return summary information for the top ``n`` populated bins."""
    return _sorted_bin_records(hist, n, ascending=False)


def bottom_bins(hist: BaseHist, n: int = 10) -> List[Dict[str, object]]:
    """Return summary information for the least ``n`` populated bins."""
    return _sorted_bin_records(hist, n, ascending=True)


def print_bin_table(records: List[Dict[str, object]], title: str) -> None:
    """Print summary table for ``records`` using ``rich``."""
    if not records:
        return
    axes = list(records[0]["bin"].keys())  # type: ignore
    table = Table(title=title)
    for ax in axes:
        table.add_column(ax)
    table.add_column("count", justify="right")
    table.add_column("fraction", justify="right")
    for r in records:
        row = [f"[{lo}, {hi})" for lo, hi in r["bin"].values()]  # type: ignore
        row.append(f"{r['count']:,}")
        row.append(f"{r['fraction']:.3f}")
        table.add_row(*row)
    Console().print(table)


def histogram_summary(hist: BaseHist) -> Dict[str, float]:
    """Return summary stats for the histogram."""
    counts = np.asarray(hist.view()).flatten()
    return _summary_from_counts(counts)


def _summary_from_counts(counts: np.ndarray) -> Dict[str, float]:
    total = int(counts.sum())
    if total == 0:
        return {
            "max_fraction": 0.0,
            "min_fraction": 0.0,
            "min_nonzero_fraction": 0.0,
            "zero_bins": int(counts.size),
        }
    fractions = counts.astype(float) / float(total)
    max_fraction = float(fractions.max())
    min_fraction = float(fractions.min())
    nonzero = fractions[counts > 0]
    min_nonzero_fraction = float(nonzero.min()) if nonzero.size > 0 else 0.0
    zero_bins = int(np.count_nonzero(counts == 0))
    return {
        "max_fraction": max_fraction,
        "min_fraction": min_fraction,
        "min_nonzero_fraction": min_nonzero_fraction,
        "zero_bins": zero_bins,
    }


def _adjacent_cells(index: Tuple[int, ...], shape: Tuple[int, ...]) -> List[Tuple[int, ...]]:
    neighbors: List[Tuple[int, ...]] = []
    for axis, size in enumerate(shape):
        for delta in (-1, 1):
            next_idx = list(index)
            next_idx[axis] += delta
            if 0 <= next_idx[axis] < size:
                neighbors.append(tuple(next_idx))
    return neighbors


def merge_sparse_cells(
    hist: BaseHist,
    min_fraction: float,
) -> Tuple[List[MergedCellGroup], Dict[str, float]]:
    """Merge adjacent n-D cells into groups until the minimum fraction is met."""
    if not 0.0 <= min_fraction <= 1.0:
        raise ValueError("min_fraction must be between 0 and 1.")

    counts = np.asarray(hist.view())
    shape = counts.shape
    flat = counts.flatten()
    total = int(flat.sum())
    if counts.size == 0:
        return [], _summary_from_counts(flat)

    axes_names = [
        ax.name if ax.name is not None else f"axis_{i}" for i, ax in enumerate(hist.axes)
    ]
    cells = list(np.ndindex(shape))
    groups: Dict[int, Dict[str, object]] = {}
    cell_to_group: Dict[Tuple[int, ...], int] = {}
    for gid, cell in enumerate(cells):
        groups[gid] = {"cells": {cell}, "count": int(counts[cell])}
        cell_to_group[cell] = gid

    if total == 0 or min_fraction <= 0.0:
        group_records = _build_group_records(groups, axes_names, total)
        summary = _summary_from_counts(
            np.array([record.count for record in group_records], dtype=int)
        )
        return group_records, summary

    def group_fraction(count: int) -> float:
        return 0.0 if total == 0 else float(count) / float(total)

    while True:
        sparse_groups = [
            gid
            for gid, info in groups.items()
            if group_fraction(int(info["count"])) < min_fraction
        ]
        if not sparse_groups:
            break
        gid = min(
            sparse_groups,
            key=lambda g: (int(groups[g]["count"]), g),
        )
        neighbor_groups: set[int] = set()
        for cell in groups[gid]["cells"]:
            for neighbor in _adjacent_cells(cell, shape):
                neighbor_groups.add(cell_to_group[neighbor])
        neighbor_groups.discard(gid)
        if not neighbor_groups:
            break
        neighbor = min(
            neighbor_groups,
            key=lambda g: (int(groups[g]["count"]), g),
        )
        groups[gid]["cells"].update(groups[neighbor]["cells"])
        groups[gid]["count"] = int(groups[gid]["count"]) + int(
            groups[neighbor]["count"]
        )
        for cell in groups[neighbor]["cells"]:
            cell_to_group[cell] = gid
        del groups[neighbor]

    group_records = _build_group_records(groups, axes_names, total)
    summary = _summary_from_counts(
        np.array([record.count for record in group_records], dtype=int)
    )
    return group_records, summary


def _build_group_records(
    groups: Dict[int, Dict[str, object]],
    axes_names: List[str],
    total: int,
) -> List[MergedCellGroup]:
    records: List[MergedCellGroup] = []
    sorted_groups = sorted(
        groups.values(),
        key=lambda info: sorted(info["cells"])[0],
    )
    for info in sorted_groups:
        cell_list = []
        for cell in sorted(info["cells"]):
            cell_list.append(
                {axis: int(cell[idx]) for idx, axis in enumerate(axes_names)}
            )
        count = int(info["count"])
        fraction = 0.0 if total == 0 else float(count) / float(total)
        records.append(
            MergedCellGroup(cells=cell_list, count=count, fraction=fraction)
        )
    return records
