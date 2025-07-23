import numpy as np
import awkward as ak
from typing import Dict, List
from pydantic import BaseModel
import yaml


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
