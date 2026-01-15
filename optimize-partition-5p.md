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
3. **Achieved** Explore per-axis override strategies to meet min/max fraction targets simultaneously.
   - Tried bins-per-axis=2 with raised jet/large-jet bins, with and without collapsing taus/photons.
   - Max fraction stayed above target (0.083-0.115) and smallest bins remained below ~1% even when sparse axes were collapsed.
4. **Failed** Pursue algorithmic alternatives (e.g., tail-capping or bin merging) to raise minimum bin fractions while keeping max fraction <= 5%.
   - Implemented adaptive per-axis bin reduction and ran on 50 files with `--ignore-axes met`.
   - Adaptive bins reduced `n_muons`, `n_jets`, `n_large_jets` to 2; max fraction 0.048 but min nonzero fraction remained ~0.000.
5. **Failed** Explore tail-capping or post-histogram bin merging to lift minimum fractions without exceeding max fraction targets.
   - Added `--tail-cap-quantile` to clip per-axis counts and ran 0.98/0.95 caps on 50 files; max fraction stayed ~0.039 but min/nonzero fractions remained ~0.000, so tail-capping did not lift sparse bins.
6. Explore post-histogram bin merging strategies to lift minimum bin fractions while keeping max fraction <= 5%.

## Steps

Steps marked as `**Done**` are finished, others are ready to be addressed in order.

Current sub-goal: TBD.

1. (Add steps for the next sub-goal here.)

## Future Ideas

The following are some ideas that might be turned into steps in the future.

- Extend the target scan to include per-axis override search or heuristics.
- Explore algorithmic alternatives to alter the binning in a non-grid way (post-histogram bin merging).
- Add a target-scan mode that varies bins-per-axis per axis for sparse vs dense axes.
- Compute and print additional histogram summaries (sparsity ratio, zero-bin count) after each run.
- Add tail-capping via per-axis quantile clipping to reduce long-tail sparsity (`--tail-cap-quantile`).
- Explore merging sparse bins or adding overflow bins after histogram build (`--merge-sparse-bins`).
- Add a CLI option to print the smallest bin fractions explicitly (e.g., `--min-bin-fraction-target`).
- Consider an option to collapse or ignore ultra-sparse axes (e.g., `n_taus`, `n_photons`) while keeping them recorded.
