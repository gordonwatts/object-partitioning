import pytest
import yaml
import awkward as ak
import numpy as np
from hist import Hist
from atlas_object_partitioning.histograms import (
    apply_tail_caps,
    compute_bin_boundaries,
    write_bin_boundaries_yaml,
    build_nd_histogram,
    histogram_boundaries,
    merge_sparse_bins,
    merge_sparse_cells,
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
    assert loaded == {"axes": boundaries, "merged_cells": None}


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


def test_compute_bin_boundaries_ignore_axes():
    data = ak.Array(
        {
            "n_muons": [0, 1, 1, 2, 2, 2, 3, 3, 4, 4],
            "n_electrons": [1, 2, 1, 0, 1, 2, 3, 3, 2, 0],
            "n_jets": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    boundaries = compute_bin_boundaries(data, ignore_axes=["n_jets"])
    assert boundaries["n_muons"] == [0, 2, 3, 4, 5]
    assert boundaries["n_electrons"] == [0, 2, 3, 4]
    assert "n_jets" not in boundaries


def test_compute_bin_boundaries_axis_overrides():
    data = ak.Array(
        {
            "n_muons": list(range(10)),
            "n_electrons": list(range(10)),
        }
    )
    boundaries = compute_bin_boundaries(
        data,
        bins_per_axis=2,
        bins_per_axis_overrides={"n_muons": 3},
    )
    assert boundaries["n_muons"] == [0, 4, 7, 10]
    assert boundaries["n_electrons"] == [0, 5, 10]


def test_compute_bin_boundaries_ignore_bad_axis():
    data = ak.Array(
        {
            "n_muons": [0, 1, 1, 2, 2, 2, 3, 3, 4, 4],
            "n_electrons": [1, 2, 1, 0, 1, 2, 3, 3, 2, 0],
            "n_jets": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    with pytest.raises(ValueError):
        compute_bin_boundaries(data, ignore_axes=["n_jets", "n_photons"])


def test_compute_bin_boundaries_override_bad_axis():
    data = ak.Array(
        {
            "n_muons": [0, 1, 2],
            "n_electrons": [1, 0, 2],
        }
    )
    with pytest.raises(ValueError):
        compute_bin_boundaries(data, bins_per_axis_overrides={"n_jets": 2})


def test_compute_bin_boundaries_override_ignored_axis():
    data = ak.Array(
        {
            "n_muons": [0, 1, 2],
            "n_electrons": [1, 0, 2],
        }
    )
    with pytest.raises(ValueError):
        compute_bin_boundaries(
            data,
            ignore_axes=["n_muons"],
            bins_per_axis_overrides={"n_muons": 2},
        )


def test_apply_tail_caps():
    data = ak.Array(
        {
            "n_jets": [0, 1, 2, 10],
            "n_muons": [0, 1, 2, 3],
        }
    )
    capped, caps = apply_tail_caps(
        data,
        ignore_axes=["n_muons"],
        tail_cap_quantile=0.5,
    )
    assert caps == {"n_jets": 1}
    assert ak.to_list(capped["n_jets"]) == [0, 1, 1, 1]
    assert ak.to_list(capped["n_muons"]) == [0, 1, 2, 3]


def test_merge_sparse_bins_1d():
    hist = Hist.new.Var([0, 1, 2, 3], name="n_muons", label="n_muons").Int64()
    hist[...] = np.array([100, 1, 100])
    merged, merges = merge_sparse_bins(hist, min_fraction=0.02, min_bins=1)
    assert merges["n_muons"] == 1
    assert np.allclose(merged.view(), np.array([101, 100]))  # type: ignore
    boundaries = histogram_boundaries(merged)
    assert boundaries["n_muons"] == [0, 2, 3]


def test_merge_sparse_bins_respects_min_bins():
    hist = Hist.new.Var([0, 1, 2], name="n_muons", label="n_muons").Int64()
    hist[...] = np.array([1, 1])
    merged, merges = merge_sparse_bins(hist, min_fraction=0.9, min_bins=2)
    assert merges["n_muons"] == 0
    assert np.allclose(merged.view(), np.array([1, 1]))  # type: ignore


def test_merge_sparse_cells_2d():
    hist = (
        Hist.new.Var([0, 1, 2], name="n_muons", label="n_muons")
        .Var([0, 1, 2], name="n_jets", label="n_jets")
        .Int64()
    )
    hist[...] = np.array([[100, 1], [1, 100]])
    groups, summary = merge_sparse_cells(hist, min_fraction=0.05)
    counts = sorted(group.count for group in groups)
    assert counts == [101, 101]
    assert summary["min_fraction"] == pytest.approx(0.5)
    assert summary["max_fraction"] == pytest.approx(0.5)
