# Plan: 5% max partition, minimize zero-count bins

## Goal

Find bin boundaries so the largest bin fraction is ~5% while minimizing the number of zero-count bins, starting from the `data18` dataset in the README.

## Read-first context

- CLI entrypoint: `src/atlas_object_partitioning/partition.py` runs the full pipeline: ServiceX scan -> parquet (optional) -> `compute_bin_boundaries` -> histogram -> top/bottom tables -> writes `bin_boundaries.yaml` and `histogram.pkl`.
- README suggests starting with `-n 10` files for a quick turn-around.
- All runs should go through the `atlas-object-partitioning` CLI; any tuning or new behavior should be exposed via CLI options or sub-commands, not ad hoc scripts.

## Iteration strategy (no code changes first)

1. **Done** **Baseline run**: Run the CLI with the data18 dataset and `-n 10`.
   - Capture the printed Top/Least bin tables.
   - Note max fraction in Top 10 and count of zero bins in Least 10.
   - Result: max fraction `0.011`, zero-bin count in Least 10: `10/10` (all zero).
   - Maintain `log.md` with run summaries (command, max fraction, zero-bin count, notes, source code changes).
2. **Done** **Increase stats**: Re-run with larger `-n` (e.g., 25, 50, 100, 0) to see stability.
   - Keep a small log: `n_files`, max fraction, zero-bin count.
   - Conclusion: use `-n 50` for future runs (fractions changed vs `-n 10`; still manageable runtime).
3. **Done** **Axis exclusions/assumptions**:
   - Do not use `met` as a partition axis since it is analysis-dependent.
   - Expect strong correlation between large-R jets and regular jets; treat them cautiously as independent axes.
   - Use `--ignore-axes met` for all CLI runs in this plan.
4. **Done** **Assess**: With `-n 50` and `--ignore-axes met`, max fraction is 0.021 (< 5%) but zeros remain high (least-10 all zero); boundary tuning is needed to reduce sparsity.
5. **Done** **Boundary tuning**: Added CLI option to control bins per axis and histogram summary output; tested bins-per-axis=2,3,4 with `--ignore-axes met` on `-n 50`. Best tradeoff so far is 3 bins (max fraction 0.039, zero bins 0).
6. **Next** **Axis-specific bin controls**: If zeros reappear or max fraction drifts with full stats, add a CLI option to set bins per axis by name (e.g., `--bins-per-axis n_jets=3 n_muons=4`) while keeping a global default. Update `compute_bin_boundaries` to accept a mapping `{axis: bins}` and fall back to the default for unspecified axes; keep `--ignore-axes met` in runs. Re-run `-n 0` with tuned axes and log max fraction + zero-bin count.

## Likely code changes (if needed)

1. **Expose binning control in CLI**:
   - Add a CLI option to set the number of bins per axis (currently fixed to 4 in `compute_bin_boundaries`).
   - Optionally add a CLI option for a minimum bin fraction or maximum bin fraction target.
   - If iterative optimization is needed, consider adding a sub-command to sweep parameters and print summary stats.
2. **Add diagnostics**:
   - Add a function to compute summary stats from `histogram.pkl`: max fraction, zero-bin count, maybe histogram sparsity ratio.
   - Print those summaries after `build_nd_histogram` for faster iteration.
3. **Boundary algorithm tuning** (guided by stats):
   - Try increasing bins per axis to reduce max fraction while monitoring zero bins.
   - Consider merging sparse bins or capping bins on axes with long tails (domain-dependent).

## Iteration loop after code changes

1. **Run/adjust cycle**:

   - Start with `-n 50`, then consider `-n 0` once behavior looks reasonable.
   - Tune bin count or boundary logic to push max fraction near 5% while minimizing zero bins.
   - Keep a small markdown table of results in `plan.md` or `notes.md`.

## Decision checkpoints

- **Stop** if max fraction <= 5% and zero-bin count is acceptably low for the chosen `n_files`.
- **Continue** if max fraction > 5% or zero bins remain high; adjust bins per axis or boundary logic.

## Next actions (once plan approved)

- Implement CLI options and summary stats.
- Run the data18 dataset iteratively, starting at `-n 50`.
