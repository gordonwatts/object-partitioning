# 5 percent max partition, raise smallest bins to ~1%

Goal: Find bin boundaries so the largest bin fraction is about 5 percent and the smallest bin fractions are on the order of ~1 percent (no ultra-sparse bins), starting from `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697`.

## Context Snapshot

This section is updated at the end of each sub-goal. It should contain enough information so no important context is lost if starting from scratch.

- Current histogram flow: `compute_bin_boundaries` -> `build_nd_histogram` -> `histogram_summary` in `src/atlas_object_partitioning/partition.py`.
- Per-axis sparse-bin merging already exists and is wired into CLI (`--merge-min-fraction`, `--merge-min-bins`); it merges along marginal axes only and did not lift min fractions (0.01/0.05 thresholds had zero merges on 50 files).
- Adjacent n-D grid-cell merging is implemented via `--merge-cell-min-fraction`; it groups neighboring cells while preserving original boundaries.
- `bin_boundaries.yaml` now includes `merged_cells` with per-group cell indices, counts, and fractions (schema change).
- Baseline run with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, `--merge-cell-min-fraction 0.01` produced merged-group max 0.039 and min 0.010 (64 groups, zero groups 0).
- Report documenting all attempts and best outputs is in `optimize-partition-5p-report.md`.

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
3. **Achieved** Explore per-axis override strategies to meet min/max fraction targets simultaneously.
   - Tried bins-per-axis=2 with raised jet/large-jet bins, with and without collapsing taus/photons.
   - Max fraction stayed above target (0.083-0.115) and smallest bins remained below ~1% even when sparse axes were collapsed.
4. **Failed** Pursue algorithmic alternatives (e.g., tail-capping or bin merging) to raise minimum bin fractions while keeping max fraction <= 5%.
   - Implemented adaptive per-axis bin reduction and ran on 50 files with `--ignore-axes met`.
   - Adaptive bins reduced `n_muons`, `n_jets`, `n_large_jets` to 2; max fraction 0.048 but min nonzero fraction remained ~0.000.
5. **Failed** Explore tail-capping or post-histogram bin merging to lift minimum fractions without exceeding max fraction targets.
   - Added `--tail-cap-quantile` to clip per-axis counts and ran 0.98/0.95 caps on 50 files; max fraction stayed ~0.039 but min/nonzero fractions remained ~0.000, so tail-capping did not lift sparse bins.
6. **Failed** Explore post-histogram bin merging strategies to lift minimum bin fractions while keeping max fraction <= 5%.
   - Implemented per-axis marginal sparse-bin merging (`--merge-min-fraction`, `--merge-min-bins`) and ran on 50 files with `--ignore-axes met`.
   - No merges occurred at thresholds 0.01 or 0.05; max fraction stayed 0.039 and min/nonzero fractions remained ~0.000, so the strategy did not lift sparse bins.
7. **Achieved** Draft adjacent grid-cell merging that preserves the grid definition but merges sparse neighboring cells; output merge groups in `bin_boundaries.yaml`.
   - Added `--merge-cell-min-fraction` to group adjacent n-D cells without altering boundaries; YAML now records merged groups.
   - Baseline run with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, `--merge-cell-min-fraction 0.01` yielded merged-group min fraction 0.010 and max 0.039 (64 groups, zero groups 0).
8. **Achieved** Write a report summarizing the problem, each attempted approach, and the best result for each (with commands and outputs), ending with the adjacent grid-cell merge results and a `describe-cells` table.
   - Wrote `optimize-partition-5p-report.md` with introduction and per-approach sections, including rerun outputs and final merged-cell table.

## Steps

Steps marked as `**Done**` are finished, others are ready to be addressed in order.

Current sub-goal: TBD.

1. (Add steps for the next sub-goal here.)

## Future Ideas

The following are some ideas that might be turned into steps in the future.

- Extend the target scan to include per-axis override search or heuristics.
- Add a target-scan mode that varies bins-per-axis per axis for sparse vs dense axes.
- Compute and print additional histogram summaries (sparsity ratio, zero-bin count) after each run.
- Add a CLI option to print the smallest bin fractions explicitly (e.g., `--min-bin-fraction-target`).
- Consider an option to collapse or ignore ultra-sparse axes (e.g., `n_taus`, `n_photons`) while keeping them recorded.
- Add README CLI output snippets for the sparse-bin merge summary line.
- Run a quick README spell/format check after documentation updates.
