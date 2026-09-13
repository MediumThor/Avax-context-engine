"""Chronological walk-forward evaluation. No random shuffle."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

from packages.evaluator.metrics import brier_score, direction_accuracy, mae, pinball_loss, rmse


@dataclass(frozen=True, slots=True)
class WalkWindow:
    train_end: int
    test_start: int
    test_end: int


@dataclass(frozen=True, slots=True)
class WalkForwardManifest:
    run_id: str
    commit: str
    data_manifest: str
    feature_schema: str
    model_config: str
    windows: tuple[dict[str, int], ...]
    metrics: dict[str, Any]
    baselines: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def chronological_windows(
    n: int, *, train_size: int, test_size: int, step: int
) -> list[WalkWindow]:
    if train_size < 1 or test_size < 1 or step < 1:
        raise ValueError("train_size, test_size, and step must be >= 1")
    if n < train_size + test_size:
        raise ValueError("series shorter than one train+test window")
    out: list[WalkWindow] = []
    train_end = train_size
    while train_end + test_size <= n:
        out.append(WalkWindow(train_end=train_end, test_start=train_end, test_end=train_end + test_size))
        train_end += step
    if not out:
        raise ValueError("no walk-forward windows produced")
    return out


def score_horizon(
    actual: Sequence[float],
    predicted: Sequence[float],
    *,
    probabilities: Sequence[float] | None = None,
    q10: Sequence[float] | None = None,
    q90: Sequence[float] | None = None,
) -> dict[str, float]:
    result = {
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
        "direction_accuracy": direction_accuracy(actual, predicted),
        "sample_count": float(len(actual)),
    }
    if probabilities is not None:
        actual_dir = [1.0 if x > 0 else 0.0 for x in actual]
        result["brier"] = brier_score(actual_dir, probabilities)
    if q10 is not None and q90 is not None:
        result["pinball_q10"] = pinball_loss(actual, q10, 0.1)
        result["pinball_q90"] = pinball_loss(actual, q90, 0.9)
        result["coverage_q10_q90"] = sum(
            float(lo <= x <= hi) for x, lo, hi in zip(actual, q10, q90)
        ) / len(actual)
    return result


def run_walk_forward(
    series: Sequence[float],
    predict: Callable[[Sequence[float], int], Sequence[float]],
    *,
    horizons: int = 10,
    train_size: int = 80,
    test_size: int = 20,
    step: int = 20,
    run_id: str = "wf-local",
    commit: str = "local",
    data_manifest: str = "unspecified",
    created_at: str = "1970-01-01T00:00:00Z",
) -> WalkForwardManifest:
    """`predict(train_prefix, horizon) -> predictions aligned to the test slice of that horizon."""
    windows = chronological_windows(len(series), train_size=train_size, test_size=test_size, step=step)
    metrics: dict[str, Any] = {}
    for h in range(1, horizons + 1):
        actual: list[float] = []
        predicted: list[float] = []
        for window in windows:
            if window.test_end + h > len(series):
                continue
            train = series[: window.train_end]
            test_actual = [
                series[i + h] - series[i] for i in range(window.test_start, window.test_end) if i + h < len(series)
            ]
            preds = list(predict(train, h))
            if len(preds) != len(test_actual):
                preds = preds[: len(test_actual)]
            actual.extend(test_actual)
            predicted.extend(preds)
        if actual:
            metrics[str(h)] = score_horizon(actual, predicted)
    return WalkForwardManifest(
        run_id=run_id,
        commit=commit,
        data_manifest=data_manifest,
        feature_schema="1",
        model_config="walkforward-v1",
        windows=tuple(asdict(w) for w in windows),
        metrics=metrics,
        baselines={},
        created_at=created_at,
    )


def assert_windows_are_causal(windows: Sequence[WalkWindow]) -> None:
    for window in windows:
        if window.test_start < window.train_end:
            raise ValueError("test overlaps train")
        if window.test_start != window.train_end:
            raise ValueError("gap between train and test is not the declared boundary")
