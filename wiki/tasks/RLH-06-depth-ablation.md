# RLH-06 — Depth walk-forward ablation

**Agent:** 06 (quant / depth walk-forward)  
**Branch:** `cursor/rlh-06-depth-8771`  
**Status:** implemented

## Scope

Run the Forecast Engine unchanged; vary only `max_depth` / halt policy via `services.harness.loop.run_loop`. Publish process-metric ablation rows. Extra depth is **not** an accuracy claim and must not change ForecastPackage numeric heads.

## API

```python
from services.evaluator.rlh.depth import ablate_depths

report = ablate_depths(memory, forecast, depths=(1, 2, 4, 8, 16), commit_sha="...")
```

Each row records:

- `max_depth`, `halt_reason`, `depth_used`, `step_count`
- `no_change_fired`
- `encoder_memory_hash`, `forecast_package_id`
- `process_metrics` from `score_trace`

`promotion_allowed` is always `false`. `notes` state that depth is process metadata, not skill.

Optional `artifact_dir` writes JSON under `artifacts/recursive/depth-ablations/` (gitignored).

## Tests

```bash
python -m pytest tests/rlh/test_depth_ablation.py -q
```

## Forbidden

- Changing ForecastPackage fields or emitting a new forecast from depth runs
- Claiming accuracy from deeper loops
- Setting `promotion_allowed` true

## Limitations

- Does not score explanation-alignment or outcome-linked metrics (Agent 07 / matured fixtures)
- Artifact directory is local-only unless copied into wiki or fixture manifests
