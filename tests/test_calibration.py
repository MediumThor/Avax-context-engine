from packages.evaluator.calibration import expected_calibration_error, interval_coverage, reliability_diagram


def test_perfectly_calibrated_has_low_ece():
    actual = [0.0, 1.0] * 50
    probs = [0.0 if y == 0 else 1.0 for y in actual]
    assert expected_calibration_error(actual, probs, bins=10) < 0.02


def test_overconfident_has_higher_ece():
    # 50/50 outcomes with 0.95/0.05 forecasts that point the wrong way.
    actual = [1.0] * 50 + [0.0] * 50
    overconfident = [0.05] * 50 + [0.95] * 50
    honest = [0.5] * 100
    assert expected_calibration_error(actual, overconfident) > expected_calibration_error(actual, honest)
    assert expected_calibration_error(actual, overconfident) > 0.4


def test_reliability_and_coverage():
    actual = [0.0, 1.0, 1.0, 0.0]
    probs = [0.1, 0.9, 0.8, 0.2]
    bins = reliability_diagram(actual, probs, bins=5)
    assert bins
    assert interval_coverage([0.0, 0.5, 1.0], [-1.0, 0.0, 0.5], [1.0, 1.0, 1.5]) == 1.0
