# Object Partitioning

![PyPI version](https://badge.fury.io/py/atlas-object-partitioning.svg)
[![Build Status](https://github.com/gordonwatts/object-partitioning/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/gordonwatts/object-partitioning/actions)

A Python package to help understand partitioning by objects. Works only on ATLAS xAOD format files (PHYS, PHYSLITE, etc.).

Writes a `parquet` file with per-event data.

## Installation

Install via **pip**:

```bash
pip install atlas-object-partitioning
```

Install via `uv`:

* If you don't have the [`uv` tool installed](https://docs.astral.sh/uv/getting-started/installation/), it is highly recommended as a way to quickly install local versions of the code without having to build custom environments, etc.

Install locally so **always available**:

```bash
uv tool install atlas-object-partitioning
atlas-object-partitioning --help
```

Update it to the most recent version with `uv tool upgrade atlas-object-partitioning`.

Or running it in an **ephemeral environment**:

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

* Use `--help` to see all options
* Specify a rucio dataset, for example, `atlas-object-partitioning mc23_13p6TeV:mc23_13p6TeV.601237.PhPy8EG_A14_ttbar_hdamp258p75_allhad.deriv.DAOD_PHYSLITE.e8514_s4369_r16083_p6697`
* Use the `-n` option to specify how many files in the dataset to run over. By default 1, specify `0` to run on everything. Some datasets are quite large. Feel free to start the transform, then re-run the same command to have it pick up where it left off. See the [dashboard](https://servicex.af.uchicago.edu/dashboard) to monitor status.

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

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the terms of the MIT license. See [LICENSE.txt](LICENSE.txt) for details.
