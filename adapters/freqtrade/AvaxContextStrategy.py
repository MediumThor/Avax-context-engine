from __future__ import annotations

import talib.abstract as ta
from pandas import DataFrame
from freqtrade.strategy import IStrategy


class AvaxContextStrategy(IStrategy):
    """FreqAI feature/target bridge only. It intentionally emits no trade entries or exits."""

    timeframe = "5m"
    can_short = False
    process_only_new_candles = True
    startup_candle_count = 240
    minimal_roi = {"0": 1000}
    stoploss = -0.99

    def feature_engineering_expand_all(self, dataframe: DataFrame, period: int, metadata: dict, **kwargs) -> DataFrame:
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
        for h in range(1, 11):
            dataframe[f"&-cum-ret-{h}"] = dataframe["close"].shift(-h) / dataframe["close"] - 1.0
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0; dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0; dataframe["exit_short"] = 0
        return dataframe
