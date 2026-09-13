from __future__ import annotations

import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class AvaxContextStrategy(IStrategy):
    """FreqAI feature/target bridge only.

    This strategy is research/read-only. It never emits trade entries or exits.
    Target columns use the FreqAI `&-` prefix and are labels, not features.
    FreqAI remains infrastructure: this file does not claim out-of-sample
    superiority over project baselines.

    WAVE2-05 journal-ready q10/q50/q90 log-return forecasts are emitted by
    ``packages.models.freqai_quantiles`` / ``FreqtradeResearchAdapter``.
    Full FreqAI training is not required for that research path. Do not change
    these ``&-cum-ret-*`` labels silently.
    """

    timeframe = "5m"
    can_short = False
    process_only_new_candles = True
    startup_candle_count = 240
    use_exit_signal = False
    minimal_roi = {"0": 1000}
    stoploss = -0.99

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["%-atr-period"] = ta.ATR(dataframe, timeperiod=period)
        dataframe["%-roc-period"] = ta.ROC(dataframe, timeperiod=period)
        dataframe["%-rel-volume-period"] = dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        dataframe["%-ret-1"] = dataframe["close"].pct_change()
        dataframe["%-range-pct"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["%-body-pct"] = (dataframe["close"] - dataframe["open"]) / dataframe["open"]
        dataframe["%-raw-volume"] = dataframe["volume"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        dataframe["%-hour"] = dataframe["date"].dt.hour / 23.0
        dataframe["%-day-of-week"] = dataframe["date"].dt.dayofweek / 6.0
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        # `&-` labels only. FreqAI must not treat these as features.
        for horizon in range(1, 11):
            dataframe[f"&-cum-ret-{horizon}"] = dataframe["close"].shift(-horizon) / dataframe["close"] - 1.0
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
