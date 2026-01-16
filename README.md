# Object Partitioning

![PyPI version](https://badge.fury.io/py/atlas-object-partitioning.svg)
[![Build Status](https://github.com/gordonwatts/object-partitioning/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/gordonwatts/object-partitioning/actions)

A Python package to help understand partitioning by objects. Works only on ATLAS xAOD format files (PHYS, PHYSLITE, etc.).

Writes a `parquet` file with per-event data, a `bin_boundaries.yaml` files, and a python pickle file with an n-dimensional histogram.

- Each *axis* is a count of PHYSLITE objects (muons, electrons, jets, etc).
- Looks at each axis and tries to divide the counts into equal bins of events.
- Then sub-divides each bin of axis 1 by axis 2 and axis 3 etc (making a
    n-dimensional histogram).
- Saves the binning and histogram to files.
- Prints out a table with the 10 largest and smallest bins.

The following are the axes:

- Jets (`AnalysisJets`)
- Large-R Jets (`AnalysisLargeRJets`)
- Electrons (`AnalysisElectrons`)
- Muons (`AnalysisMuons`)
- Taus (`AnalysisTauJets`)
- Photons (`AnalysisPhotons`)
- MissingET (`MET_Core_AnalysisMET`) - In ATLAS,`met` is analysis dependent. This is just the first object in the `MissingET` container, with `met()` called on that object.

Use `atlas-object-partitioning partition --help` to see available options. Set
`--bins-per-axis` to control how many bins are used per axis (defaults to 4).

Tail-capping optionally clips per-axis counts at a quantile before binning. This reduces
long tails by replacing values above the chosen quantile with the cap value, which can
help stabilize boundary selection when a few extreme events dominate an axis.

Tail-capping examples:

```bash
# Cap each axis at the 98th percentile before building boundaries
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --bins-per-axis 3 --tail-cap-quantile 0.98

# Combine tail-capping with target scan to see summary stats
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --tail-cap-quantile 0.95 \
  --target-min-fraction 0.01 --target-max-fraction 0.05 \
  --target-bins-min 3 --target-bins-max 3
```

Sparse-bin merging optionally merges adjacent bins per axis after building the
histogram. It uses marginal counts for each axis and repeatedly merges the
smallest bins into their nearest neighbor until each marginal bin fraction
meets the threshold or the axis hits the minimum bin count.

Sparse-bin merging examples:

```bash
# Merge marginal bins below 1% along each axis, keep at least 2 bins per axis
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --bins-per-axis 3 --merge-min-fraction 0.01 \
  --merge-min-bins 2

# Combine target scan with a stricter merge threshold
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --target-min-fraction 0.0 --target-max-fraction 1.0 \
  --target-bins-min 3 --target-bins-max 3 --merge-min-fraction 0.05 \
  --merge-min-bins 2
```

Adjacent grid-cell merging groups sparse n-D cells (sharing a face) without
changing the bin boundaries. The merged groups are written to
`bin_boundaries.yaml`, and the CLI prints a merged-cell summary with the total
grid cells, how many were combined, and the final group count.

`bin_boundaries.yaml` schema:

- `axes`: map of axis name to list of bin edges (inclusive lower, exclusive upper).
- `merged_cells`: optional summary of merged n-D cell groups when
  `--merge-cell-min-fraction` is used.
  - `min_fraction`: the fraction threshold used for grouping.
  - `groups`: list of merged groups.
    - `cells`: list of grid cell indices, keyed by axis name (0-based).
    - `count`: total event count in the merged group.
    - `fraction`: total event fraction for the merged group.

Pretty-print merged cells from the CLI:

```bash
# Summarize merged cell groups with index ranges per axis
atlas-object-partitioning describe-cells bin_boundaries.yaml

# Include bin edge ranges with the index ranges
atlas-object-partitioning describe-cells bin_boundaries.yaml --show-values

# Sort groups by size (count) descending
atlas-object-partitioning describe-cells bin_boundaries.yaml --sort-by-size
```

Update merged cell counts using an existing binning and merged-cell grouping
(the input YAML must already contain `merged_cells.groups`), e.g. when the
binning was defined on a smaller scan but you want counts from a larger scan:

```bash
atlas-object-partitioning repartition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  bin_boundaries.yaml -n 500 -o bin_boundaries.repartition.yaml
```

Adjacent grid-cell merging example:

```bash
# Merge sparse n-D cells below 1% into adjacent groups
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --bins-per-axis 3 --merge-cell-min-fraction 0.01
```

If you are trying to balance max bin fraction (~5%) with minimum group size
(~1%), the adjacent grid-cell merge example above is the recommended starting
point.

Adaptive binning examples (greedily reduces bins per axis to approach target min/max
fractions):

```bash
# Baseline adaptive search targeting 1% min nonzero, 5% max fraction
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --bins-per-axis 3 \
  --adaptive-bins --adaptive-min-fraction 0.01 --adaptive-max-fraction 0.05

# Constrain the minimum bins per axis and keep explicit overrides fixed
atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 \
  -n 50 --ignore-axes met --bins-per-axis 4 \
  --bins-per-axis-override n_jets=4 --bins-per-axis-override n_large_jets=4 \
  --adaptive-bins --adaptive-min-fraction 0.005 --adaptive-max-fraction 0.05 \
  --adaptive-min-bins 2
```

An example output:

```python
$ atlas-object-partitioning partition data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697 -n 10
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ n_jets     ┃ n_large_jets ┃ n_electrons ┃ n_muons    ┃ n_taus     ┃ n_photons  ┃ met          ┃ count ┃ fraction ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [0.0, 1.0) │ [0.0, 1.0) │ [0.0, 3.0) │ [0.0, 11.0)  │ 4,611 │    0.011 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [1.0, 2.0)  │ [0.0, 1.0) │ [1.0, 2.0) │ [0.0, 3.0) │ [0.0, 11.0)  │ 3,605 │    0.009 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [0.0, 1.0) │ [0.0, 1.0) │ [0.0, 3.0) │ [11.0, 18.0) │ 3,401 │    0.008 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [1.0, 2.0)  │ [0.0, 1.0) │ [1.0, 2.0) │ [0.0, 3.0) │ [11.0, 18.0) │ 3,107 │    0.008 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [1.0, 2.0) │ [0.0, 1.0) │ [0.0, 3.0) │ [0.0, 11.0)  │ 3,047 │    0.007 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [1.0, 2.0) │ [0.0, 1.0) │ [0.0, 3.0) │ [11.0, 18.0) │ 2,708 │    0.007 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [1.0, 2.0) │ [1.0, 2.0) │ [0.0, 3.0) │ [0.0, 11.0)  │ 2,353 │    0.006 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [0.0, 1.0) │ [0.0, 1.0) │ [0.0, 3.0) │ [18.0, 26.0) │ 2,141 │    0.005 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [0.0, 1.0)  │ [1.0, 2.0) │ [1.0, 2.0) │ [0.0, 3.0) │ [11.0, 18.0) │ 2,139 │    0.005 │
│ [0.0, 6.0) │ [0.0, 1.0)   │ [1.0, 2.0)  │ [0.0, 1.0) │ [1.0, 2.0) │ [0.0, 3.0) │ [18.0, 26.0) │ 1,964 │    0.005 │
└────────────┴──────────────┴─────────────┴────────────┴────────────┴────────────┴──────────────┴───────┴──────────┘
                                                    Least 10 bins                                                     
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┓
┃ n_jets     ┃ n_large_jets ┃ n_electrons ┃ n_muons    ┃ n_taus     ┃ n_photons   ┃ met           ┃ count ┃ fraction ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━┩
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [0.0, 1.0) │ [1.0, 2.0) │ [4.0, 5.0)  │ [26.0, 160.0) │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [0.0, 1.0) │ [2.0, 7.0) │ [5.0, 17.0) │ [11.0, 18.0)  │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [0.0, 1.0) │ [2.0, 7.0) │ [4.0, 5.0)  │ [26.0, 160.0) │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [0.0, 1.0) │ [2.0, 7.0) │ [3.0, 4.0)  │ [26.0, 160.0) │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [1.0, 2.0) │ [2.0, 7.0) │ [5.0, 17.0) │ [11.0, 18.0)  │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [1.0, 2.0) │ [2.0, 7.0) │ [4.0, 5.0)  │ [26.0, 160.0) │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [2.0, 7.0) │ [2.0, 7.0) │ [4.0, 5.0)  │ [0.0, 11.0)   │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [2.0, 7.0) │ [2.0, 7.0) │ [3.0, 4.0)  │ [26.0, 160.0) │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [2.0, 7.0) │ [2.0, 7.0) │ [3.0, 4.0)  │ [11.0, 18.0)  │     0 │    0.000 │
│ [0.0, 6.0) │ [1.0, 3.0)   │ [2.0, 8.0)  │ [2.0, 7.0) │ [2.0, 7.0) │ [0.0, 3.0)  │ [11.0, 18.0)  │     0 │    0.000 │
└────────────┴──────────────┴─────────────┴────────────┴────────────┴─────────────┴───────────────┴───────┴──────────┘
Histogram summary: max fraction 0.011, zero bins 16,384
```

## Installation

Install via **pip**:

```bash
pip install atlas-object-partitioning
```

Run via `uv`:

- If you don't have the [`uv` tool installed](https://docs.astral.sh/uv/getting-started/installation/), it is highly recommended as a way to quickly install local versions of the code without having to build custom environments, etc.

Install locally so **always available**:

```bash
uv tool install atlas-object-partitioning
atlas-object-partitioning --help
```

Update it to the most recent version with `uv tool upgrade atlas-object-partitioning`.

Or running it in an **ephemeral environment** (recommended for intermittent or one-off use):

```bash
uvx atlas-object-partitioning --help
```

Or install from **source**:

```bash
git clone https://github.com/gordonwatts/object-partitioning.git
cd atlas-object-partitioning
pip install .
```

## Usage

You'll need a `servicex.yaml` file with a valid token to use the ServiceX backend. See [here to help you get started](https://servicex-frontend.readthedocs.io/en/stable/connect_servicex.html).

From the **command line**.

- Use `atlas-object-partitioning partition --help` to see all partition options
- Specify a rucio dataset, for example, `atlas-object-partitioning partition mc23_13p6TeV:mc23_13p6TeV.601237.PhPy8EG_A14_ttbar_hdamp258p75_allhad.deriv.DAOD_PHYSLITE.e8514_s4369_r16083_p6697`
- Use the `-n` option to specify how many files in the dataset to run over. By default 1, specify `0` to run on everything. Some datasets are quite large. Feel free to start the transform, then re-run the same command to have it pick up where it left off. See the [dashboard](https://servicex.af.uchicago.edu/dashboard) to monitor status.
- Use `--adaptive-bins` to greedily reduce bins per axis toward target min/max fractions. Note that adaptive mode cannot be combined with `--target-min-fraction` or `--target-max-fraction`.

If you wish, you can also use it as a **library**:

```python
from atlas_object_partitioning.partition import partition_objects
from atlas_object_partitioning.scan_ds import scan_dataset

# Example: Partition a list of objects
data = [...]  # your data here
partitions = partition_objects(data, num_partitions=4)

# Scan a dataset
results = scan_dataset('object_counts.parquet')
```

## Goal

We want to come up with a set of simple square partitions that will have 5% as the largest partition and a minimal number of zeros in the partition.

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the terms of the MIT license. See [LICENSE.txt](LICENSE.txt) for details.
