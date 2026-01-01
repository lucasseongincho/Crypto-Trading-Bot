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

1.  **`strategy.py` (The Brain):** Contains the mathematical logic for finding sweeps and gaps. Start here to see the "Why."
2.  **`main.py` (The Engine):** The central hub that runs the loop, refreshes balances, and triggers the other modules.
3.  **`risk.py` (The Accountant):** Our safety net. It calculates position sizes based on our **$XX.XX** balance to ensure we only risk **X%** per trade.
4.  **`trader.py` (The Executioner):** Handles the actual API calls to Coinbase to place Buy/Sell/Stop orders.
5.  **`auth.py` & `client.py` (Security):** Manage the connection and credential extraction from the JSON key file.

### 3. Environment Setup
To run the bot locally, you will need:
* **Python 3.10+**
* **Virtual Environment:** `python -m venv venv`
* **API Credentials:**
    * `cdp_api_key.json`: Your Coinbase CDP keys - You can download it from Coinbase when you make an account.
    * `.env`: Your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

## 🧪 How to Run Backtesting
Follow these steps to verify the strategy against historical data.

### 1. Download Historical Data
Fetch 5-minute candles directly from Coinbase.
```bash
python download_data.py --pair ETH-USD --start 2025-01-02 --end 2025-12-31
```
### 2. Run the Backtest Simulation
Process the CSV through the simulation engine. This sorts data chronologically and generates **`trade_journal.csv`**.
```bash
python run_backtest.py --file ETH-USD_candles.csv
```
### 3. Generate Performance Report
Analyze the journal to see win rate, profit factor, and drawdowns.
```bash
python performance_summary.py
```

## 📊 Outcome So Far (One-Year Test)

**Period:** Jan 2, 2025 – Dec 31, 2025 | **Pair:** ETH-USD | **Initial Balance:** $1,000

During this period, the Ethereum market was in a consistent downtrend. While a passive investor would have lost money, the bot successfully generated a profit by identifying shorting opportunities.

| Metric | Buy & Hold (The Market) | SMC Trading Bot (Our Bot) |
| :--- | :--- | :--- |
| **Price Movement** | $3,411.52 → $2,970.33 | **$1,000.00 → $1,267.45** |
| **Total Return** | -12.93% (Loss) | **+26.75% (Profit)** |
| **Max Drawdown** | ~ -30.00% | **-15.87%** |
| **Final Equity** | $870.70 | **$1,267.45** |
| **Performance Gap** | Baseline | **+39.68% Over Market** |

### Key Performance Highlights
* **Bear Market Alpha:** The bot generated a **+26.75%** return while the underlying asset fell by nearly 13%.
* **Superior Risk Management:** The bot achieved these gains with a Maximum Drawdown of only **15.87%**, significantly lower than the volatility experienced by holding the asset.
* **Short-Selling Success:** Profits were largely driven by the bot's ability to "Short" the market during structural shifts and FVG fills in a declining environment.

## 📈 Upcoming Features
* [ ] **Backtesting Journal:** Tracking dates, entry/exit costs, and drawdown.
* [ ] **Flexible Data Downloader:** Custom date ranges for historical analysis.
* [ ] **AWS Deployment:** Moving to an EC2 instance for 24/7 uptime.
