# Run log

## Purpose

Track CLI runs, settings, and summary stats (max fraction, zero-bin count) for `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697`.

## Runs

- 2025-02-14 00:00 Baseline run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 10`. Max fraction 0.011; least-10 zeros 10/10.
- 2025-02-14 00:00 Run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 10` and `--ignore-axes met`. Max fraction 0.028; least-10 zeros 10/10; fractions increased vs baseline.
- 2025-02-14 00:00 Run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 50` and `--ignore-axes met`. Max fraction 0.021; least-10 zeros 10/10; longer runtime.
- 2026-01-13 00:00 Run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`. Max fraction 0.039; zero bins 0 (least-10 non-zero).
- 2026-01-13 00:00 Run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 2`. Max fraction 0.102; zero bins 0 (least-10 non-zero).
- 2026-01-13 00:00 Run on `data18_13TeV:data18_13TeV.periodAllYear.physics_Main.PhysCont.DAOD_PHYSLITE.grp18_v01_p6697` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 4`. Max fraction 0.021; zero bins 27 (least-10 includes zeros).
- 2026-01-14 03:31 Added per-axis bin override parsing and validation; compute_bin_boundaries now accepts overrides.
- 2026-01-14 03:32 Attempted CLI run with -n 50, --ignore-axes met, --bins-per-axis 3, overrides n_taus=2/n_photons=2; failed because ServiceX tried to read /workspaces/object-partitioning/servicex.yaml but it is a directory (IsADirectoryError).
- 2026-01-14 03:32 Marked step 6 done (axis-specific bin overrides) and added a new step to resolve ServiceX config before rerunning -n 50.
- 2026-01-14 03:49 Added checkpoint note to plan: overrides implemented; runs blocked by servicex.yaml directory.
- 2026-01-14 04:24 Checked for ServiceX config; no `servicex.yaml` found in repo or home, so split step to request config before rerun.
- 2026-01-14 04:26 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`; max fraction 0.039, zero bins 0.
- 2026-01-14 04:31 Updated plan goal to target smallest bin fractions around ~1% and added tuning steps to raise the minimum bin size.
- 2026-01-14 04:32 Adjusted step 11 wording to be general about rerunning with updated bin settings.
- 2026-01-14 04:36 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, overrides `n_taus=2`, `n_photons=2`; max fraction 0.068, zero bins 0 (least bins ~0.000).
- 2026-01-14 04:36 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, overrides `n_jets=4`, `n_large_jets=4`, `n_taus=2`, `n_photons=2`; max fraction 0.055, zero bins 3.
- 2026-01-14 04:36 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, overrides `n_jets=4`, `n_large_jets=3`, `n_taus=2`, `n_photons=2`; max fraction 0.055, zero bins 0 (least bins ~0.000).
- 2026-01-14 04:36 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, overrides `n_jets=5`, `n_large_jets=4`, `n_taus=2`, `n_photons=2`; max fraction 0.055, zero bins 3.
- 2026-01-14 04:36 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--bins-per-axis 3`, overrides `n_jets=4`, `n_large_jets=3`, `n_electrons=4`, `n_muons=4`, `n_taus=2`, `n_photons=2`; max fraction 0.055, zero bins 0 (least bins ~0.000).
- 2026-01-14 04:36 Marked plan step 10 done after multiple tuning attempts and added new steps to try collapsing or ignoring sparse axes.
- 2026-01-14 05:27 Added CLI options to scan bins-per-axis against target min/max bin fractions and report min fractions.
- 2026-01-14 05:27 Ran `atlas-object-partitioning` with `-n 50`, `--ignore-axes met`, `--target-min-fraction 0.01`, `--target-max-fraction 0.05`, `--target-bins-min 2`, `--target-bins-max 4`; scan showed max 0.102 (bins=2), min fractions ~0.000 for bins=3/4, selected bins=3 with max 0.039.
- 2026-01-14 05:27 Updated plan steps to reflect the new target-fraction scan option and next actions.
- 2026-01-14 05:39 Ran target scan with `-n 50`, `--ignore-axes met`, overrides `n_taus=1`, `n_photons=1`, scan 1-5 with targets 0.01/0.05; selected bins-per-axis=2 with max 0.152 and min 0.017 (no target met).
- 2026-01-14 05:39 Ran target scan with `-n 50`, `--ignore-axes met --ignore-axes n_taus --ignore-axes n_photons`, scan 1-5 with targets 0.01/0.05; selected bins-per-axis=2 with max 0.152 and min 0.017 (no target met).
- 2026-01-15 06:53 Attempted CLI run with --dataset/partition syntax; atlas-object-partitioning expects ds_name positional, so the run failed with option/argument errors.
- 2026-01-15 06:53 Ran atlas-object-partitioning with -n 50, --ignore-axes met, --bins-per-axis 2, overrides n_jets=3 n_large_jets=3; max fraction 0.083, zero bins 0 (min fractions ~0.000).
- 2026-01-15 06:53 Ran atlas-object-partitioning with -n 50, --ignore-axes met, --bins-per-axis 2, overrides n_taus=1 n_photons=1 n_jets=3 n_large_jets=3; max fraction 0.115, zero bins 0 (min fractions ~0.003-0.009).
- 2026-01-15 06:53 Ran atlas-object-partitioning with -n 50, --ignore-axes met, --bins-per-axis 2, overrides n_taus=1 n_photons=1 n_jets=4 n_large_jets=4; max fraction 0.092, zero bins 0 (min fractions ~0.000-0.003).
- 2026-01-15 06:53 Marked sub-goal 3 achieved after per-axis override tests; started sub-goal 4 to explore algorithmic alternatives and reset Steps section accordingly.
- 2026-01-15 07:43 Documented algorithmic alternatives (tail-capping, bin merging, axis-weighted binning) and selected axis-weighted binning as the next approach.
- 2026-01-15 07:44 Added adaptive bin reduction CLI options and greedy per-axis search for target min/max fractions.
- 2026-01-15 07:45 Ran adaptive bins with -n 50, --ignore-axes met, --bins-per-axis 3; adaptive reduced n_muons/n_jets/n_large_jets to 2; max fraction 0.048, min nonzero ~0.000, zero bins 0.
- 2026-01-15 07:45 Marked sub-goal 4 failed (adaptive bins did not raise min fractions) and queued tail-capping/bin-merging as next sub-goal.
- 2026-01-15 08:10 Added steps to explore tail-capping via per-axis quantile clipping.
- 2026-01-15 08:11 Added tail-cap quantile support, including histogram capping helper and tests.
- 2026-01-15 08:12 Ran pytest for tail-cap test coverage (tests/atlas_object_partitioning/test_histograms.py -k tail_caps).
- 2026-01-15 08:12 Ran atlas-object-partitioning with -n 50, --ignore-axes met, --bins-per-axis 3, --tail-cap-quantile 0.98; caps n_electrons=2 n_jets=17 n_large_jets=3 n_muons=2 n_photons=7 n_taus=3; max fraction 0.039, zero bins 0 (least bins ~0.000).
- 2026-01-15 08:13 Ran atlas-object-partitioning with -n 50, --ignore-axes met, --tail-cap-quantile 0.95, target scan 3-3 (targets 0.01/0.05); caps n_electrons=1 n_jets=14 n_large_jets=3 n_muons=2 n_photons=6 n_taus=2; max fraction 0.039, min fraction 0.000, min nonzero 0.000, zero bins 0.
- 2026-01-15 08:13 Marked tail-capping sub-goal failed and queued post-histogram bin merging as the next sub-goal.
