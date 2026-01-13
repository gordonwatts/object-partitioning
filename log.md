# Run log

## Purpose

Track CLI runs, settings, and summary stats (max fraction, zero-bin count) for the data18 dataset.

## Runs

- 2025-02-14: data18, `-n 10`, no ignore-axes, baseline from README-style run. Max fraction 0.011; least-10 zeros 10/10.
- 2025-02-14: data18, `-n 10`, `--ignore-axes met`. Max fraction 0.028; least-10 zeros 10/10. Fractions increased vs baseline (met removed).
- 2025-02-14: data18, `-n 50`, `--ignore-axes met`. Completed after longer timeout. Max fraction 0.021; least-10 zeros 10/10.
- 2026-01-13: data18, `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`. Max fraction 0.039; zero bins 0 (least-10 non-zero).
- 2026-01-13: data18, `-n 50`, `--ignore-axes met`, `--bins-per-axis 2`. Max fraction 0.102; zero bins 0 (least-10 non-zero).
- 2026-01-13: data18, `-n 50`, `--ignore-axes met`, `--bins-per-axis 4`. Max fraction 0.021; zero bins 27 (least-10 includes zeros).
