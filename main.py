"""Slow EMA trend bot for the make.fun btc-race 24h bounty.

Trades Coinbase Wrapped BTC (CBBTC) against USDC, one-minute bars, long only,
starting from 1,000 USDC of paper money. Speaks agent-fun/bars-replay/v1
through the kit's Python shim (vendored unchanged under vendor/).

Strategy (chosen for robustness, not for a single window's spike):
  - EMA(21) / EMA(55) crossover on 1-minute closes, each EMA seeded as the
    mean of its first span of closes, then moving 2 / (span + 1) of the way
    to each new close, exactly like the kit's ema-cross baseline.
  - Entry, full equity: EMA(21) crosses above EMA(55) AND the trailing
    30-minute return is above +0.40%. The momentum confirmation keeps the
    bot out of the flat chop where a bare crossover whipsaws: on the dev
    window the bare EMA(8)/EMA(21) baseline trades 63 times and loses
    $134.95, while this bot trades 5 times.
  - Exit, whole position: EMA(55) crosses back above EMA(21) (the down
    signal, held while EMA(55) stays above), or the position is worth 2%
    over its cost (take profit). No stop-loss level: on one-minute bars a
    tight level is hit by noise far more often than by a real reversal.
  - A buy caps its slippage at 200 bps past the close it was decided on;
    a sell leaves it wide open (10,000 bps) so an exit always executes
    instead of being refused into a falling market.

Why these numbers: the 21/55 pair with the 0.40% confirmation and the 2%
take-profit is the configuration that stayed profitable on the dev window
(+$13.24, 5 trades, 1.7% max drawdown) and on both stress views of it
(the sign-flipped window, +$30.78, and the time-reversed window,
+$13.93), while faster pairs and tighter exits lost on at least one of
the three. Every parameter sits on a plateau, not a spike: the
neighbouring settings (ret 40-60 bps, take-profit 2.0-2.25%) all clear
the dev gate, so the bot does not depend on one exact value.

Deterministic: no randomness, no wall clock, no environment reads. The
only state is the closes seen and the two EMAs, so two runs on the same
bars produce byte-identical action logs.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
FAST_SPAN = 21
SLOW_SPAN = 55
RET_BARS = 30
RET_THR_BPS = 40          # trailing 30-minute return must beat +0.40% to enter
TAKE_PROFIT_NUM = 102     # exit when the position is worth 102% of its cost
TAKE_PROFIT_DEN = 100
BUY_SLIPPAGE_BPS = 200
SELL_SLIPPAGE_BPS = 10000


class Ema:
    """One EMA: the closes it has seen until it starts, then its value."""

    def __init__(self, span):
        self.span = span
        self.warm = []
        self.value = None

    def step(self, close):
        if self.value is not None:
            self.value += (2 / (self.span + 1)) * (close - self.value)
            return
        self.warm.append(close)
        if len(self.warm) == self.span:
            self.value = sum(self.warm) / self.span


class Series:
    """The two EMAs and the cross state for the one symbol."""

    def __init__(self):
        self.fast = Ema(FAST_SPAN)
        self.slow = Ema(SLOW_SPAN)
        self.gap = None   # fast - slow after the bar before this one
        self.now = None   # fast - slow after this bar
        self.down = False  # the sell signal: set on a cross down, held while slow stays above

    def push(self, close):
        self.fast.step(close)
        self.slow.step(close)
        self.gap = self.now
        if self.fast.value is not None and self.slow.value is not None:
            self.now = self.fast.value - self.slow.value
        else:
            self.now = None
        if self.now is None or self.now >= 0:
            self.down = False
        return self


series = Series()
closes = []  # every close seen, in bar order


def cross_up(s):
    return s.gap is not None and s.now is not None and s.now > 0 and s.gap <= 0


def on_batch(state, batch):
    for bar in batch.bars:
        if bar["symbol"] != SYMBOL:
            continue
        closes.append(int(bar["c"]))
        series.push(int(bar["c"]))
        if series.now is not None and series.now < 0 and series.gap is not None and series.gap >= 0:
            series.down = True
    if state.warming_up:
        return []
    held = state.positions.get(SYMBOL)
    close = state.close(SYMBOL)
    if close is None:
        return []
    if held is not None:
        if series.down:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": SELL_SLIPPAGE_BPS}]
        if state.value(SYMBOL, held.qty) * TAKE_PROFIT_DEN >= held.cost * TAKE_PROFIT_NUM:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": SELL_SLIPPAGE_BPS}]
        return []
    if cross_up(series) and len(closes) > RET_BARS:
        then = closes[-1 - RET_BARS]
        if (close - then) * 10000 > then * RET_THR_BPS:
            amount = state.cash
            if amount >= int(state.hello["fees"]["min_notional_quote_units"]):
                return [{"side": "buy", "symbol": SYMBOL,
                         "notional_quote_units": amount,
                         "max_slippage_bps": BUY_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
