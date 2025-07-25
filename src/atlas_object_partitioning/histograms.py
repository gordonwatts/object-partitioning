import numpy as np
import awkward as ak
from typing import Dict, List
from pydantic import BaseModel
import yaml
from typing import Tuple
from rich.table import Table
from rich.console import Console
from hist import Hist
import pickle


def _compute_boundaries(values: ak.Array) -> List[int]:
    """Compute 3 boundary values that split the distribution into 4 bins.

    Parameters
    ----------
    values: ak.Array
        Array of values for a single axis.
    Returns
    -------
    List[int]
        List of boundary values (upper edge of 1st, 2nd, 3rd quartiles).
    """
    if len(values) == 0:
        return []
    min_val = int(ak.min(values))
    max_val = int(ak.max(values))
    bins = np.arange(min_val, max_val + 2)
    hist, edges = np.histogram(values, bins=bins)
    cdf = np.cumsum(hist)
    quarter = cdf[-1] / 4
    boundaries: List[int] = []
    for i in range(1, 4):
        idx = int(np.searchsorted(cdf, quarter * i))
        boundaries.append(int(edges[idx + 1]))

    # Always return [min, ...boundaries..., max+1]
    boundaries = [min_val] + boundaries + [max_val + 1]

    # Make sure all boundaries entries are unique
    boundaries = sorted(set(boundaries))

    return boundaries


def compute_bin_boundaries(data: ak.Array) -> Dict[str, List[int]]:
    """Compute bin boundaries for all axes in the awkward array."""
    result: Dict[str, List[int]] = {}
    for axis in data.fields:
        result[axis] = _compute_boundaries(data[axis])
    return result


class BinBoundaries(BaseModel):
    axes: Dict[str, List[int]]


def write_bin_boundaries_yaml(boundaries: Dict[str, List[int]], file_path: str) -> None:
    """Write the bin boundaries to ``file_path`` in YAML format."""
    data = BinBoundaries(axes=boundaries)
    with open(file_path, "w") as f:
        yaml.safe_dump(data.model_dump(), f)


def build_nd_histogram(
    data: ak.Array, boundaries: Dict[str, List[int]]
) -> Hist:
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
    h_builder = h_builder.Int64()
    h = h_builder()

    # Fill with event counts
    fill_dict = {ax: ak.to_numpy(data[ax]) for ax in axes}
    h.fill(**fill_dict)

    return h


def write_histogram_pickle(hist: Hist, file_path: str) -> None:
    """Persist the histogram to disk using :mod:`pickle`."""
    with open(file_path, "wb") as f:
        pickle.dump(hist, f)


def load_histogram_pickle(file_path: str) -> Hist:
    """Load a histogram previously written with :func:`write_histogram_pickle`."""
    with open(file_path, "rb") as f:
        hist = pickle.load(f)
    return hist


def _sorted_bin_records(
    hist: Hist,
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
    axes_names = [ax.name if ax.name is not None else f"axis_{i}" for i, ax in enumerate(hist.axes)]
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


def top_bins(hist: Hist, n: int = 10) -> List[Dict[str, object]]:
    """Return summary information for the top ``n`` populated bins."""
    return _sorted_bin_records(hist, n, ascending=False)


def bottom_bins(hist: Hist, n: int = 10) -> List[Dict[str, object]]:
    """Return summary information for the least ``n`` populated bins."""
    return _sorted_bin_records(hist, n, ascending=True)


def print_bin_table(records: List[Dict[str, object]], title: str) -> None:
    """Print summary table for ``records`` using ``rich``."""
    if not records:
        return
    axes = list(records[0]["bin"].keys())
    table = Table(title=title)
    for ax in axes:
        table.add_column(ax)
    table.add_column("count", justify="right")
    table.add_column("fraction", justify="right")
    for r in records:
        row = [f"[{lo}, {hi})" for lo, hi in r["bin"].values()]
        row.append(str(r["count"]))
        row.append(f"{r['fraction']:.3f}")
        table.add_row(*row)
    Console().print(table)

