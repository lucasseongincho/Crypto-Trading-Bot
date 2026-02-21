🎯 SMC Sniper Bot
=================

A Python-based algorithmic trading bot that executes a **Smart Money Concepts (SMC)** strategy on cryptocurrency markets (BTC-USD). The bot features a robust Object-Oriented architecture, a fully offline backtesting engine, and a live paper-trading module integrated with the Coinbase API and Telegram.

✨ Key Features
--------------

-   **SMC Strategy Logic:** Automatically scans 5-minute and 6-hour candles for liquidity sweeps and Fair Value Gaps (FVG).

-   **Dynamic Risk Management:** Automatically sizes positions to risk exactly 1% of the current account balance per trade, targeting a 1:1.5 Risk/Reward ratio.

-   **Trailing Kill Switch:** A dynamic, account-level safety net that locks in profits. If the account drops 30% from its all-time high, the bot immediately shuts down to protect capital.

-   **Paper Trading Mode:** Pulls live market data from Coinbase but simulates order execution to safely forward-test strategies.

-   **Telegram Integration:** Sends real-time trade alerts (Open, Close, Stop-Loss moves) and hourly heartbeat status updates directly to your phone.

-   **Standardized Logging:** Records all trades, durations, and targets into a clean `trade_journal.csv` for easy analysis.

* * * * *

📂 Project Architecture
-----------------------

The bot has been strictly refactored into 6 core modules:

1.  **`live_main.py`** - The Live/Paper Execution Engine. Connects to Coinbase, manages the trading loop, and handles live position monitoring.

2.  **`main.py`** - The Backtest Research Lab. Reads historical CSV data to rapidly test the strategy without network delays.

3.  **`strategy.py`** - *The Brain.* Contains the `SMCStrategy` class which analyzes price action and generates Buy/Sell signals.

4.  **`risk.py`** - *The Accountant.* Contains the `RiskManager` class which handles position sizing, virtual balance tracking, and PnL math.

5.  **`journal.py`** - *The Logger.* Formats and writes detailed trade data to `trade_journal.csv`.

6.  **`test_risk.py`** - Unit tests to ensure the RiskManager math is executing flawlessly.

* * * * *

⚙️ Setup & Installation
-----------------------

### 1\. Prerequisites

-   Python 3.10+

-   Pandas, Requests, Python-dotenv

-   Coinbase SDK (for API connection)

### 2\. Virtual Environment Setup

To keep your dependencies clean, it is highly recommended to run the bot inside a virtual environment:


```
python -m venv venv
venv\Scripts\activate

```

*(Note: If you are on Mac/Linux, use `source venv/bin/activate` instead).*

### 3\. Environment Setup & API Credentials

To run the bot locally, you will need to set up your keys:

-   **`cdp_api_key.json`**: Your Coinbase CDP keys. You can download this file directly from Coinbase when you create an API account. Place it in your project's root folder.

-   **`.env`**: Create this file in the root directory and add your Telegram credentials:


```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

```

* * * * *

🚀 Usage
--------

### 1\. Download Historical Data

Fetch 5-minute candles directly from Coinbase to use for your offline backtests.

```
python download_data.py --pair BTC-USD --start 2026-02-01 --end 2026-02-21

```

### 2\. Running a Backtest

To test the strategy against the historical data you just downloaded, use `main.py`:

```
python main.py --file BTC-USD_candles.csv

```

### 3\. Running the Live/Paper Bot

To start scanning the live markets, simply run the main execution file. (To switch between Paper Money and Real Money, toggle the `PAPER_MODE` boolean inside the script).

```
python live_main.py

```

### 4\. Running Unit Tests

To verify the integrity of the risk management math before deploying:

```
python test_risk.py

```

* * * * *

⚠️ Disclaimer
-------------

**This software is for educational and research purposes only.** Algorithmic trading involves significant risk of loss. The dynamic kill switch and risk management features are mitigations, not guarantees. Always test extensively in Paper Mode before risking real capital.