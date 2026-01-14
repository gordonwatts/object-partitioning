# 5 percent max partition, minimize zero-count bins

Goal: Find bin boundaries so the largest bin fraction is about 5 percent while minimizing zero-count bins, starting from `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697`.

## Checkpoint

As of 2026-01-14, axis-specific bin overrides are implemented and validated, but CLI runs are blocked because `servicex.yaml` is a directory. Restart runs after fixing ServiceX configuration.

## Constraints

Be sure to always obey the following constraints as you formulate and execute the steps.

- Always write to the file `optimize-partition-5p-log.md`. Each entry should contain a time stamp, and should be made anytime something significant happens:
  - You make a real modification to the source code
  - You run the code to obtain an answer
  - Any time you complete a step or create new steps.
  - Format your log entries as a markdown list, starting with date and tme and then a short 1-line description of what you've done.
- Use the `atlas-object-partitioning` CLI for all runs; expose tuning and new behavior through CLI options or sub-commands.
- Use `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` as the baseline dataset for this goal.
- Use `--ignore-axes met` for all runs in this plan.
- Treat large-R jets and regular jets as potentially correlated when deciding axes to bin.

## Hints

The following hints may be helpful:

- `-n 50` is a reasonable balance of stability vs runtime for iteration.
- `--bins-per-axis 3` gave the best tradeoff so far (max fraction 0.039, zero bins 0).
- `--bins-per-axis 2` raised max fraction to 0.102; `--bins-per-axis 4` introduced 27 zero bins.
- Stop once max fraction is <= 5 percent and zero-bin count is acceptably low for the chosen `n_files`.
- 50 files can take quite a while to run the first time - so be patient (minutes!).

## Steps

Steps marked as `**Done**` are finished, others are ready to be addressed in order.

1. **Done** Run a baseline CLI pass on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 10`; capture max fraction and least-bin zeros. Result: max fraction 0.011; least-10 zeros 10/10.
2. **Done** Increase statistics with larger `-n` values (25, 50, 100, 0) to assess stability. Result: fractions changed vs `-n 10`; `-n 50` chosen for future runs.
3. **Done** Decide axis exclusions and assumptions. Result: ignore `met` via `--ignore-axes met` and note large-R jet correlation.
4. **Done** Assess with `-n 50` and `--ignore-axes met`. Result: max fraction 0.021 (< 5 percent), but least-10 bins still all zero.
5. **Done** Tune bins-per-axis using the CLI and review histogram summaries. Result: bins-per-axis=3 yields max fraction 0.039 and zero bins 0; bins-per-axis=2 yields 0.102; bins-per-axis=4 yields 0.021 with 27 zero bins.
6. **Done** Add axis-specific bin controls to keep a global default while allowing per-axis overrides. Result: CLI accepts `--bins-per-axis-override AXIS=INT`, validated in `compute_bin_boundaries`.
7. Resolve ServiceX config error (`servicex.yaml` is a directory) or provide a valid config path; re-run with 50 files (`-n 50`) and log max fraction plus zero-bin count.
8. Re-evaluate whether the 5 percent target and zero-bin threshold are met at full stats; if not, adjust binning logic and iterate.

## Future Ideas

The following are some ideas that might be turned into steps in the future.

- Add a CLI option for min/max bin fraction targets or a sweep mode for parameter exploration.
- Compute and print additional histogram summaries (sparsity ratio, zero-bin count) after each run.
- Explore merging sparse bins or capping bins for axes with long tails.
