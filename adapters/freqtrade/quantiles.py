"""Research command surface for WAVE2-05 quantile forecasts.

Never constructs ``freqtrade trade`` or any order API. Full FreqAI training is
not required: the leakage-safe wrapper in ``packages.models.freqai_quantiles``
emits a journal-ready payload.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Sequence

from adapters.freqtrade.constants import (
    NO_BASELINE_CLAIM,
    PINNED_COMMIT,
    QUANTILE_RESEARCH_COMMAND,
)
from adapters.freqtrade.safety import ResearchOnlyViolation

FORBIDDEN_CLI_FLAGS = frozenset(
    {
        "--trade",
        "--live",
        "--execute",
        "--place-order",
        "--stake",
        "--dry-run-false",
    }
)


def emit_research_quantile_forecast(
    candles: Sequence[Any],
    as_of: datetime | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    from packages.models.freqai_quantiles import emit_quantile_forecast

    payload = dict(emit_quantile_forecast(candles, as_of=as_of, **kwargs))
    payload["upstream_freqtrade_commit"] = PINNED_COMMIT
    payload["freqai_beats_baselines"] = None
    payload["performance_claim"] = payload.get("performance_claim") or NO_BASELINE_CLAIM
    payload["research_command"] = QUANTILE_RESEARCH_COMMAND
    return payload


def refuse_live_cli(argv: Sequence[str]) -> None:
    lowered = [str(item).lower() for item in argv]
    for flag in FORBIDDEN_CLI_FLAGS:
        if flag in lowered:
            raise ResearchOnlyViolation(f"{flag} is forbidden on the research quantile command")
    if any(token in {"trade", "buy", "sell", "execute"} for token in lowered):
        raise ResearchOnlyViolation("live trading tokens are forbidden on the research quantile command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=QUANTILE_RESEARCH_COMMAND,
        description=(
            "Research-only AVAX 5m q10/q50/q90 emitter. "
            "Does not place orders. Does not claim baseline improvement."
        ),
    )
    parser.add_argument(
        "--help-research",
        action="store_true",
        help="Print the research-only contract and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    refuse_live_cli(args)
    parser = build_parser()
    parsed, _unknown = parser.parse_known_args(args)
    print(
        json.dumps(
            {
                "command": QUANTILE_RESEARCH_COMMAND,
                "mode": "research-read-only",
                "live_trading": False,
                "dry_run": True,
                "max_open_trades": 0,
                "stake_amount": 0,
                "freqai_beats_baselines": None,
                "performance_claim": NO_BASELINE_CLAIM,
                "pinned_commit": PINNED_COMMIT,
                "usage": (
                    "Call emit_research_quantile_forecast(candles, as_of=T) "
                    "from Python. Candle JSON stdin is not implemented in this increment."
                ),
                "help_research": bool(getattr(parsed, "help_research", False)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
