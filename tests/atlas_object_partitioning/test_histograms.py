import yaml
import awkward as ak
from atlas_object_partitioning.histograms import (
    compute_bin_boundaries,
    write_bin_boundaries_yaml,
)


def test_compute_bin_boundaries(tmp_path):
    data = ak.Array(
        {
            "n_muons": [0, 1, 1, 2, 2, 2, 3, 3, 4, 4],
            "n_electrons": [1, 2, 1, 0, 1, 2, 3, 3, 2, 0],
        }
    )
    boundaries = compute_bin_boundaries(data)
    assert boundaries["n_muons"] == [2, 3, 4]
    assert boundaries["n_electrons"] == [2, 2, 3]

    out_file = tmp_path / "bounds.yaml"
    write_bin_boundaries_yaml(boundaries, out_file)
    with open(out_file) as f:
        loaded = yaml.safe_load(f)
    assert loaded == {"axes": boundaries}
