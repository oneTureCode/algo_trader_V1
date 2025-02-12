# Algo Trader V1

This is an algorithmic trading system designed for backtesting and live trading. The system allows you to create and test trading strategies, backtest them using historical data, and execute live trades using various exchange APIs.

## Project Structure

```
C:\Users\tee\Desktop\coding_dir\algo_trader_V1
│
|-- backtester.py        # Backtesting logic for strategies
|-- config.py            # Configuration file for API keys, account settings, and parameters
|-- data_handler.py      # Handles data fetching, cleaning, and storage
|-- Data_store           # Folder for storing raw and processed data (e.g., CSV files)
|-- live_trader.py       # Live trading logic and execution
|-- main.py              # Entry point for the system (CLI interface)
|-- requirements.txt     # Project dependencies
|-- results              # Folder for storing backtest results, logs, and performance metrics
|-- strategies           # Folder containing strategy scripts
```

## Installation

To get started, clone the repository and install the required dependencies.

### 1. Clone the repository

```bash
git clone <repository-url>
cd algo_trader_V1
```

### 2. Install dependencies

Create a virtual environment and install the dependencies listed in `requirements.txt`.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure the system

Edit the `config.py` file to add your API keys, account details, and any other configuration settings required for your exchange(s) and strategies.

### 4. Running the system

You can run the system in either **backtest** or **live** mode using the command line interface (CLI).

#### Backtest Mode

To run a backtest, use the following command:

```bash
python main.py --mode backtest
```

This will execute the backtest using historical data and the strategies defined in the `strategies` folder.

#### Live Trading Mode

To start live trading, use the following command:

```bash
python main.py --mode live
```

This will execute live trades based on the strategies and API configurations in the `config.py` file.

## Components

### 1. **backtester.py**

This script handles the backtesting logic, simulating trades based on historical data and evaluating the performance of different strategies.

- Can be run from `main.py` in backtest mode.
- Outputs performance metrics and equity curves in the `results` folder.

### 2. **config.py**

The configuration file where all the settings are stored. This includes:

- API keys for exchanges (e.g., MEXC, Binance).
- Account details (e.g., trading pairs, account balances).
- Strategy parameters (e.g., stop-loss, take-profit, lot size).

### 3. **data_handler.py**

Responsible for fetching, cleaning, and storing market data. It can retrieve historical data from exchanges and save it in the `Data_store` folder.

### 4. **live_trader.py**

Handles live trading logic, including executing orders and managing trades in real-time based on the active strategy.

### 5. **main.py**

The entry point of the system. It allows you to choose between backtesting and live trading modes through the command line interface (CLI).

### 6. **strategies Folder**

Contains individual strategy scripts (e.g., `strategy1.py`, `strategy2.py`). Each strategy can be dynamically loaded by the system for backtesting or live trading.

### 7. **results Folder**

Stores the output from backtests, including performance metrics, logs, and equity curves.

### 8. **requirements.txt**

Contains a list of all the Python dependencies required to run the project, including libraries for backtesting, data handling, and live trading.

## Future Enhancements

- **Streamlit UI**: A user interface for managing configurations, strategies, and visualizing results.
- **Strategy Optimization**: Implement functionality to optimize strategy parameters for better performance.
- **Error Handling**: Improve error handling for live trading (e.g., network failures, API issues).
- **Unit Tests**: Add unit tests for each component to ensure system stability.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"# algo_trader_V1" 
#   a l g o _ t r a d e r _ V 1  
 #   a l g o _ t r a d e r _ V 1  
 "# algo_trader_V1" 
