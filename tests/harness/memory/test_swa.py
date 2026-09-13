from services.harness.memory import SlidingWindow, merge_query


def test_window_never_exceeds_w_and_evicted_remain_in_trace():
    swa = SlidingWindow(window_w=3)
    durable: list[dict] = []
    hashes = []
    for i in range(8):
        hashes.append(swa.append({"t": i + 1, "kind": "RETRIEVE"}, durable_steps=durable))
    assert len(swa) == 3
    assert len(durable) >= 8
    replay = SlidingWindow(window_w=3)
    replay_hashes = []
    for i in range(8):
        replay_hashes.append(replay.append({"t": i + 1, "kind": "RETRIEVE"}))
    assert hashes == replay_hashes


def test_fact_conflict_prefers_encoder_memory():
    swa = SlidingWindow(16)
    swa.append({"t": 1, "kind": "SYNTHESIZE", "claimed_4h": "bullish"})
    memory = {"timeframe_slices": {"4h": {"regime": "bearish"}}, "zone_ids": ["zone-8"], "health": "valid"}
    state = {"regime_reading": {"4h": "bullish"}}
    merged = merge_query("regime", encoder_memory=memory, swa=swa, state=state)
    assert merged["value"]["timeframe_slices"]["4h"]["regime"] == "bearish"
    both = merge_query("other", encoder_memory=memory, swa=swa, state=state)
    assert "encoder_wins_parent_regime" in both["contradictions"]
    assert both["value"]["resolved_4h"] == "bearish"
