# Object Partitioning

![PyPI version](https://badge.fury.io/py/atlas-object-partitioning.svg)
[![Build Status](https://github.com/yourusername/atlas-object-partitioning/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/atlas-object-partitioning/actions)

A Python package to help understand partitioning by objects. Works only on ATLAS xAOD format files (PHYS, PHYSLITE, etc.).

Writes a `parquet` file with per-event data.

## Installation

Install via pip:

```bash
pip install atlas-object-partitioning
```

Or install from source:

```bash
git clone https://github.com/yourusername/atlas-object-partitioning.git
cd atlas-object-partitioning
pip install .
```

## Usage

```python
from atlas_object_partitioning.partition import partition_objects
from atlas_object_partitioning.scan_ds import scan_dataset

# Example: Partition a list of objects
data = [...]  # your data here
partitions = partition_objects(data, num_partitions=4)

# Scan a dataset
results = scan_dataset('object_counts.parquet')
```

See the [documentation](https://github.com/yourusername/atlas-object-partitioning) for more details and advanced usage.

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the terms of the MIT license. See [LICENSE.txt](LICENSE.txt) for details.
