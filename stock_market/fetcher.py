import yfinance as yf
import pandas as pd
def fetcher(ticker_symbol, period):
    try:
        ticker = yf.Ticker(ticker_symbol)
        historical_data = ticker.history(period=period)
        if historical_data.empty:
            return {'error': f"No data found for ticker '{ticker_symbol}'."}
        timestamps = historical_data.index.tz_localize(None).tolist()
        close_prices = historical_data['Close'].tolist()
        latest_price = close_prices[-1]
        oldest_price = close_prices[0]
        percent_change = round((latest_price - oldest_price) / oldest_price * 100, 2)
        return {'x_axis': timestamps, 'y_axis': close_prices, 'current_price': latest_price, 'percent_change': percent_change}
    except Exception as e:
        return {'error': str(e)}
