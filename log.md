# Run log

## Purpose

Track CLI runs, settings, and summary stats (max fraction, zero-bin count) for the data18 dataset.

## Runs

- 2025-02-14: data18, `-n 10`, no ignore-axes, baseline from README-style run. Max fraction 0.011; least-10 zeros 10/10.
- 2025-02-14: data18, `-n 10`, `--ignore-axes met`. Max fraction 0.028; least-10 zeros 10/10. Fractions increased vs baseline (met removed).
- 2025-02-14: data18, `-n 50`, `--ignore-axes met`. Completed after longer timeout. Max fraction 0.021; least-10 zeros 10/10.
