import yaml

from atlas_object_partitioning.partition import _calc_usage_fraction


def test_calc_usage_fraction_basic():
    boundaries = {
        "n_electrons": [0, 1, 3],
        "n_muons": [0, 2, 4],
    }
    merged_groups = [
        {"cells": [{"n_electrons": 0, "n_muons": 0}], "fraction": 0.4},
        {"cells": [{"n_electrons": 1, "n_muons": 0}], "fraction": 0.3},
        {"cells": [{"n_electrons": 1, "n_muons": 1}], "fraction": 0.3},
    ]
    usage = _calc_usage_fraction(boundaries, merged_groups, {"n_electrons": 1})
    assert usage == 0.6

    usage = _calc_usage_fraction(
        boundaries, merged_groups, {"n_electrons": 1, "n_muons": 2}
    )
    assert usage == 0.3


def test_calc_usage_fraction_out_of_range_cut():
    boundaries = {"n_electrons": [0, 1, 2]}
    merged_groups = [
        {"cells": [{"n_electrons": 0}], "fraction": 0.7},
        {"cells": [{"n_electrons": 1}], "fraction": 0.3},
    ]
    usage = _calc_usage_fraction(boundaries, merged_groups, {"n_electrons": 2})
    assert usage == 0.0


def test_calc_usage_yaml_roundtrip(tmp_path):
    data = {
        "axes": {"n_electrons": [0, 1, 3], "n_muons": [0, 2, 4]},
        "merged_cells": {
            "groups": [
                {
                    "cells": [{"n_electrons": 0, "n_muons": 0}],
                    "count": 10,
                    "fraction": 0.4,
                },
                {
                    "cells": [{"n_electrons": 1, "n_muons": 1}],
                    "count": 5,
                    "fraction": 0.6,
                },
            ]
        },
    }
    path = tmp_path / "bin_boundaries.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f)

    with open(path) as f:
        loaded = yaml.safe_load(f)

    boundaries = loaded["axes"]
    groups = loaded["merged_cells"]["groups"]
    usage = _calc_usage_fraction(boundaries, groups, {"n_electrons": 1})
    assert usage == 0.6
