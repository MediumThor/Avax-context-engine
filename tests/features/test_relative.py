from packages.features import assemble_features
from tests.features.conftest import series, utc


def test_relative_return_is_avax_minus_btc():
    start = utc(2026, 1, 1)
    avax = series(40, start=start, price=10.0, step=0.1)
    btc = series(40, start=start, price=100.0, step=0.1, symbol="BTCUSDT")
    eth = series(40, start=start, price=50.0, step=0.05, symbol="ETHUSDT")
    snap = assemble_features(avax, utc(2026, 1, 1, 3, 20), btc_5m=btc, eth_5m=eth)
    # identical additive steps on different bases => different log returns
    assert snap.values["rel_avax_btc_logret_1"] is not None
    assert snap.values["rel_avax_eth_logret_1"] is not None
    assert snap.values["btc_5m_logret_1"] is not None
    assert snap.values["eth_5m_logret_12"] is not None


def test_relative_features_ignore_unclosed_cross_asset_bars():
    start = utc(2026, 1, 1)
    avax = series(30, start=start, price=8.0, step=0.01)
    btc = series(30, start=start, price=90_000.0, step=10.0, symbol="BTCUSDT")
    as_of = utc(2026, 1, 1, 2, 20)
    baseline = assemble_features(avax, as_of, btc_5m=btc)
    # mark a still-open future BTC bar closed with a huge print; assembler must ignore it at as_of
    from dataclasses import replace

    noisy = []
    for c in btc:
        if c.open_time >= utc(2026, 1, 1, 2, 20):
            noisy.append(replace(c, close=1.0, open=1.0, high=2.0, low=0.5, volume=1e9, is_closed=True))
        else:
            noisy.append(c)
    mutated = assemble_features(avax, as_of, btc_5m=noisy)
    assert baseline.values["rel_avax_btc_logret_1"] == mutated.values["rel_avax_btc_logret_1"]
    assert baseline.values["btc_5m_logret_1"] == mutated.values["btc_5m_logret_1"]
