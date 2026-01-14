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
