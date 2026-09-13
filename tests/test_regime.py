from packages.context_engine.regime import classify_regime, parent_child_reading


def test_one_opposite_child_does_not_flip_parent_bear():
    parent = classify_regime(
        ema_order=-0.8,
        swing=-0.7,
        momentum=-0.4,
        volume=-0.2,
        parent_regime=None,
        prior="bearish",
    )
    assert parent.final_state == "bearish"
    child = classify_regime(
        ema_order=0.6,
        swing=0.3,
        momentum=0.4,
        volume=0.1,
        parent_regime="bearish",
        prior="neutral",
    )
    assert child.final_state != "bullish"
    assert child.final_state in {"transition_up", "neutral", "bearish"}
    assert "parent_bearish" in parent_child_reading("bearish", child.final_state)


def test_component_scores_are_exposed():
    scores = classify_regime(ema_order=-1.0, swing=-1.0, momentum=0.0, volume=0.0, parent_regime="bearish")
    payload = scores.to_dict()
    assert set(payload) >= {"trend_score", "structure_score", "momentum_score", "volume_score", "parent_alignment", "final_state"}
    assert payload["parent_alignment"] < 0
