# Binance Futures Trading Bot

A command-line tool for trading Binance Futures with Market, Limit, and Stop-Limit orders.

## Installation

```
# Clone the repo
git clone https://github.com/javets70/Primetrade-Binance-Bot.git
cd Primetrade-Binance-Bot

# Install with uv
uv sync
```

## Configuration

Create a `.env` file:

```
API_KEY=your_binance_api_key
SECRET_KEY=your_binance_secret_key
```

## Usage

```
# Get balance
binance-bot balance

# Get price
binance-bot price BTCUSDT

# Place market order
binance-bot market BTCUSDT BUY 0.001

# Place limit order
binance-bot limit BTCUSDT BUY 0.001 50000

# Place stop-limit order
binance-bot stop-limit BTCUSDT SELL 0.001 44900 45000

# View orders
binance-bot orders

# Enable verbose logging
binance-bot -v balance

# Use live trading (⚠️ real money!)
binance-bot --live balance
```

**Note**: Testnet is enabled by default. Use `--live` flag for real trading.
