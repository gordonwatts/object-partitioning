# 5 percent max partition, raise smallest bins to ~1%

Goal: Find bin boundaries so the largest bin fraction is about 5 percent and the smallest bin fractions are on the order of ~1 percent (no ultra-sparse bins), starting from `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697`.

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

## Sub-Goals

Sub-Goals marked as `**Achieved**` are finished.

1. **Achieved** Establish baseline partitioning with axis exclusions and bin-per-axis tuning.
2. **Achieved** Implement axis-specific bin overrides and target fraction scanning.
3. Explore per-axis override strategies to meet min/max fraction targets simultaneously.

## Steps

Steps marked as `**Done**` are finished, others are ready to be addressed in order.

Current sub-goal: Explore per-axis override strategies or algorithmic alternatives to meet min/max fraction targets simultaneously.

1. **Done** Run a baseline CLI pass on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 10`; capture max fraction and least-bin zeros. Result: max fraction 0.011; least-10 zeros 10/10.
2. **Done** Increase statistics with larger `-n` values (25, 50, 100, 0) to assess stability. Result: fractions changed vs `-n 10`; `-n 50` chosen for future runs.
3. **Done** Decide axis exclusions and assumptions. Result: ignore `met` via `--ignore-axes met` and note large-R jet correlation.
4. **Done** Assess with `-n 50` and `--ignore-axes met`. Result: max fraction 0.021 (< 5 percent), but least-10 bins still all zero.
5. **Done** Tune bins-per-axis using the CLI and review histogram summaries. Result: bins-per-axis=3 yields max fraction 0.039 and zero bins 0; bins-per-axis=2 yields 0.102; bins-per-axis=4 yields 0.021 with 27 zero bins.
6. **Done** Add axis-specific bin controls to keep a global default while allowing per-axis overrides. Result: CLI accepts `--bins-per-axis-override AXIS=INT`, validated in `compute_bin_boundaries`.
7. **Done** Provide a valid ServiceX config path or `servicex.yaml` file (request from user if missing). Result: `servicex.yaml` confirmed at `/workspaces/servicex.yaml`.
8. **Done** Once ServiceX config is available, re-run with 50 files (`-n 50`) and log max fraction plus zero-bin count. Result: `--bins-per-axis 3` yields max fraction 0.039, zero bins 0.
9. **Done** Re-evaluate whether the 5 percent target and zero-bin threshold are met at full stats; if not, adjust binning logic and iterate. Result: targets met at `-n 50`, no further adjustments needed.
10. **Done** Tune binning to raise the smallest bin fractions toward ~1% while keeping max fraction <= 5% and avoiding zero bins. Start with `--bins-per-axis 2` and/or per-axis overrides to merge sparse axes (e.g., photons, taus). Result: Tried multiple override combinations (taus/photons to 2, jets/large-jets/electrons/muons up to 4/5). Max fraction stayed ~0.055 and smallest bins remained ~0.000; zero bins varied 0-3.
11. **Done** Add a CLI option to target min/max bin fractions by scanning bins-per-axis, then run it once at `-n 50`. Result: Added `--target-min-fraction/--target-max-fraction` scan; ran with 2-4 bins and targets 0.01/0.05, no candidate met targets; selected bins-per-axis=3 with max fraction 0.039 and min fraction 0.000.
12. **Done** Use the new target options with axis collapsing (`--bins-per-axis-override n_taus=1 --bins-per-axis-override n_photons=1`) or ignoring axes (`--ignore-axes n_taus --ignore-axes n_photons`), and widen the scan range to see if min fraction reaches ~1% without exceeding max 5%. Result: Both collapse and ignore runs selected bins-per-axis=2 with max fraction 0.152 and min fraction 0.017; neither met the max 5% target.
13. Decide whether to explore per-axis overrides on jets/large-jets to reduce max fraction while keeping min fraction >=1% (e.g., keep bins-per-axis=2 globally, raise jets/large-jets bins to 3), or switch to a new algorithmic strategy (tail-capping or weighted binning).

## Future Ideas

The following are some ideas that might be turned into steps in the future.

- Extend the target scan to include per-axis override search or heuristics.
- Explore algorithmic alternatives to alter the binning an a non-grid like way (so combine some bins, etc.).
- Add a target-scan mode that varies bins-per-axis per axis for sparse vs dense axes.
- Compute and print additional histogram summaries (sparsity ratio, zero-bin count) after each run.
- Explore merging sparse bins or capping bins for axes with long tails.
- Add a CLI option to print the smallest bin fractions explicitly (e.g., `--min-bin-fraction-target`).
- Consider an option to collapse or ignore ultra-sparse axes (e.g., `n_taus`, `n_photons`) while keeping them recorded.
- Explore axis-weighted binning that prioritizes flattening dense axes (jets, large jets) before splitting sparse ones.
