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
4. Pursue algorithmic alternatives (e.g., tail-capping or bin merging) to raise minimum bin fractions while keeping max fraction <= 5%.

## Steps

Steps marked as `**Done**` are finished, others are ready to be addressed in order.

Current sub-goal: Pursue algorithmic alternatives (e.g., tail-capping or bin merging) to raise minimum bin fractions while keeping max fraction <= 5%.

1. Identify a feasible algorithmic change (tail-capping, bin merging, or axis-weighted binning) that can be exposed via CLI without breaking existing workflows. Do this by listing the changes that would be need to be made in each case.
2. Compare the feasability, and pick one. The other ideas should be placed in the Future Ideas section.
3. Follow implementation plan and test.
4. Prototype the change behind a CLI option and run with `-n 50`, `--ignore-axes met` on the baseline dataset to evaluate max/min fractions.

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
