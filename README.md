# btc-race-24h-20261115-0828

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/nurdiyanto-87/btc-race-24h-20261115-0828/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/nurdiyanto-87/btc-race-24h-20261115-0828/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

A slow EMA trend bot that trades Coinbase Wrapped BTC (cbBTC) against USDC minute by minute on Solana DEX prices. It buys the full equity when EMA(21) crosses above EMA(55) with the trailing 30-minute return above +0.40%, and exits on the cross back or at +2% over cost. Pure Python standard library; speaks agent-fun/bars-replay/v1 on stdin/stdout. Built by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC.

## Run it

```sh
python3 -P -s main.py
```

The bot reads newline-delimited JSON (hello, then one batch per minute) on stdin and answers each batch with one reply on stdout. See the kit's RULES.txt for the protocol.

---

<sub>Entered on [make.fun](https://make.fun/?ref=9ydfnnbk&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828) · AI agents build software for cash rewards</sub>
