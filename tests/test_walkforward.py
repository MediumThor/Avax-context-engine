from packages.evaluator.walkforward import (
    assert_windows_are_causal,
    chronological_windows,
    run_walk_forward,
)


def test_windows_never_score_the_past_with_the_future():
    windows = chronological_windows(200, train_size=80, test_size=20, step=20)
    assert_windows_are_causal(windows)
    for earlier, later in zip(windows, windows[1:]):
        assert later.train_end > earlier.train_end
        assert earlier.test_end <= later.test_start or earlier.test_end <= later.train_end


def test_walk_forward_zero_predictor_on_synthetic_drift():
    series = [float(i) for i in range(200)]

    def predict(train, horizon):
        return [0.0] * 20

    manifest = run_walk_forward(
        series,
        predict,
        horizons=2,
        train_size=80,
        test_size=20,
        step=20,
        run_id="wf-test",
        created_at="2026-09-13T00:00:00Z",
    )
    assert manifest.windows
    assert "1" in manifest.metrics
    assert manifest.metrics["1"]["sample_count"] > 0
    payload = manifest.to_dict()
    assert payload["run_id"] == "wf-test"
    assert payload["metrics"]["1"]["mae"] > 0
