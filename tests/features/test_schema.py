from datetime import timezone

from packages.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, assemble_features, feature_schema_version
from tests.features.conftest import series, utc


def test_feature_schema_version_is_nonempty_string():
    assert isinstance(FEATURE_SCHEMA_VERSION, str)
    assert FEATURE_SCHEMA_VERSION == "avax.features.mtf.v1"
    assert feature_schema_version() == FEATURE_SCHEMA_VERSION
    assert FEATURE_SCHEMA_VERSION.startswith("avax.features.")


def test_feature_names_are_unique_and_stable():
    assert FEATURE_NAMES
    assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES))
    assert FEATURE_NAMES[0] == "avax_5m_logret_1"
    assert "avax_15m_rsi14" in FEATURE_NAMES
    assert "avax_1h_atr14" in FEATURE_NAMES
    assert "avax_4h_ema20_dist" in FEATURE_NAMES
    assert "avax_1d_vol_z_24" in FEATURE_NAMES
    assert "rel_avax_btc_logret_1" in FEATURE_NAMES
    assert "rel_avax_eth_corr_24" in FEATURE_NAMES


def test_snapshot_carries_schema_version_and_full_vector():
    candles = series(80)
    as_of = utc(2026, 1, 1, 6, 40)
    snap = assemble_features(candles, as_of)
    assert snap.feature_schema_version == FEATURE_SCHEMA_VERSION
    assert set(snap.values) == set(FEATURE_NAMES)
    assert len(snap.feature_vector()) == len(FEATURE_NAMES)
    payload = snap.to_dict()
    assert payload["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert payload["as_of"].endswith("+00:00") or payload["as_of"].endswith("Z")
    assert snap.as_of.tzinfo is not None
    assert snap.as_of.tzinfo.utcoffset(snap.as_of) == timezone.utc.utcoffset(snap.as_of)
