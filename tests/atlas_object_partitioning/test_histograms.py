import yaml
import awkward as ak
import numpy as np
from atlas_object_partitioning.histograms import (
    compute_bin_boundaries,
    write_bin_boundaries_yaml,
    build_nd_histogram,
    write_histogram_pickle,
    load_histogram_pickle,
    top_bins,
)


def test_compute_bin_boundaries(tmp_path):
    data = ak.Array(
        {
            "n_muons": [0, 1, 1, 2, 2, 2, 3, 3, 4, 4],
            "n_electrons": [1, 2, 1, 0, 1, 2, 3, 3, 2, 0],
        }
    )
    boundaries = compute_bin_boundaries(data)
    assert boundaries["n_muons"] == [0, 2, 3, 4, 5]
    assert boundaries["n_electrons"] == [0, 2, 3, 4]

    out_file = tmp_path / "bounds.yaml"
    write_bin_boundaries_yaml(boundaries, out_file)
    with open(out_file) as f:
        loaded = yaml.safe_load(f)
    assert loaded == {"axes": boundaries}


def test_compute_bin_boundaries_all_zero():
    data = ak.Array({"n_muons": [0, 0, 0, 0]})
    boundaries = compute_bin_boundaries(data)
    assert boundaries["n_muons"] == [0, 1]


def test_compute_bin_boundaries_all_zero_and_one():
    data = ak.Array({"n_muons": [0, 0, 1, 0]})
    boundaries = compute_bin_boundaries(data)
    assert boundaries["n_muons"] == [0, 1, 2]


def test_histogram_build_and_io(tmp_path):
    data = ak.Array(
        {
            "n_muons": [0, 1, 1, 2, 0],
            "n_electrons": [1, 0, 1, 2, 1],
        }
    )
    bounds = compute_bin_boundaries(data)
    hist = build_nd_histogram(data, bounds)
    assert hist.view().sum() == len(data)  # type: ignore

    file = tmp_path / "hist.pkl"
    write_histogram_pickle(hist, file)  # type: ignore
    hist2 = load_histogram_pickle(file)

    assert hist2.axes[0].size == hist.axes[0].size
    assert np.allclose(hist2.view(), hist.view())  # type: ignore
    assert hist2.view().sum() == len(data)  # type: ignore

    top = top_bins(hist2, n=1)[0]
    assert "count" in top and "fraction" in top
