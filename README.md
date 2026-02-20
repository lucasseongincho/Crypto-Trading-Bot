# 🤖 Crypto-Trading-Bot (SMC Edition)

This project is a crypto trading bot designed for Coinbase Advanced Trade, utilizing **Smart Money Concepts (SMC)** to identify high-probability institutional footprints in the market.

---

## 🗺️ Contributor Roadmap
Before we start coding, please follow this path to understand how the bot "thinks" and how the project is structured.

### 1. The "Big Picture" (Trading Concepts)
Our bot doesn't just look at price; it looks for **Institutional Intent**. To understand our entry logic, please research these three terms:

* **Liquidity Sweeps:** How "Smart Money" triggers retail Stop Losses to gather buy/sell orders before a major move.
* **Market Structure Shift (MSS):** How we identify the exact moment a trend reverses on a lower time frame.
* **Fair Value Gaps (FVG) & Order Blocks:** The specific "inefficiencies" and "footprints" left behind by large orders where we look to enter.

### 2. The Code Hierarchy (Reading Order)
Read the files in this order to understand the logic flow:

1. **`live_main.py` (The Production Engine):** **Run this for actual trading.** It connects to live data, manages 24/7 execution, and sends Telegram updates.
2. **`main.py` (The Research Lab):** **Now for Backtesting ONLY.** It is hard-locked to prevent accidental live trades. Use this to test new ideas on historical data.
3. **`strategy.py` (The Brain):** Shared logic used by both the live engine and the research lab to find signals.
4. **`risk.py` (The Accountant):** Shared risk module that calculates position sizes, 1.5R Take Profits, and Breakeven stops.
5. **`journal.py`:** Automatically logs every completed trade for performance analysis.

### 3. Environment Setup
To run the bot locally, you will need:
* **Python 3.10+**
* **Virtual Environment:** `python -m venv venv` then `venv\Scripts\activate`
* **API Credentials:**
    * `cdp_api_key.json`: Your Coinbase CDP keys - You can download it from Coinbase when you make an account.
    * `.env`: Your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

---

## 📡 Live Monitoring & Telegram
The bot is designed for "set it and forget it" operation with real-time feedback via Telegram.

* **Heartbeat Messages:** Every candle scan, the bot sends a status update to confirm it is still online, showing current balance and total trades.
* **Trade Alerts:** Instant notifications for **Trade Entry**, **Safety Reached (Move to Breakeven)**, and **Final Exit**.
* **Power Alerts:** Notifies you immediately if the bot script starts or restarts.

---

## 🧪 How to Run Research (Backtesting)
Follow these steps to verify the strategy against historical data.

### 1. Download Historical Data
Fetch 5-minute candles directly from Coinbase.
```bash
python download_data.py --pair BTC-USD --start 2025-01-02 --end 2025-12-31
```
### 2. Run the Backtest Simulation
Process the CSV through the simulation engine. This sorts data chronologically and generates **`trade_journal.csv`**.
```bash
python main.py --file BTC-USD_candles.csv
```
### 3. Generate Performance Report of the lastest file
Analyze the journal to see win rate, profit factor, and drawdowns.
```bash
python performance_summary.py --coin ETH
```

## 📄 How to Run Paper testing
Follow these steps to verify the strategy against live data using fake money.

### 1. Paper Mode Setting
Set "PAPER_MODE = True" in live_main.py

### 2. Run main.py
```bash
python live_main.py
```

## 📊 Outcome So Far (One-Year Test)

**Period:** Jan 2, 2025 – Dec 31, 2025 | **Pair:** ETH-USD | **Initial Balance:** $1,000

During this period, the Ethereum market was in a consistent downtrend. While a passive investor would have lost money, the bot successfully generated a profit by identifying shorting opportunities.

| Metric | Buy & Hold (The Market) | SMC Trading Bot (Our Bot) |
| :--- | :--- | :--- |
| **Price Movement** | $3,411.52 → $2,970.33 | $3,411.52 → $2,970.33 |
| **Total Return** | -12.93% (Loss) | **+168.605% (Profit)** |
| **Max Drawdown** | ~ -30.00% | **-21.56%** |
| **Final Equity** | $870.70 | **$2686.05** |
| **Performance Gap** | Baseline | **+181.535% Over Market** |

### Key Performance Highlights
* **Bear Market Alpha:** The bot generated a **+168.605%** return while the underlying asset fell by nearly 13%.
* **Superior Risk Management:** The bot achieved these gains with a Maximum Drawdown of only **21.56%**, significantly lower than the volatility experienced by holding the asset.
* **Short-Selling Success:** Profits were largely driven by the bot's ability to "Short" the market during structural shifts and FVG fills in a declining environment.

## 📈 Upcoming Features
* [x] **Telegram Integration:** Real-time heartbeat and trade notifications.
* [x] **Dual-Mode Architecture:** Separation of Research (`main.py`) and Execution (`live_main.py`).
* [ ] **Remote Commands:** Ability to "Emergency Stop" or "Reboot" the bot via Telegram chat.
* [ ] **Dedicated Hardware:** Migrating to a 24/7 Mini PC for maximum uptime.
