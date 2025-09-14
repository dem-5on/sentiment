import ccxt
import requests
import pandas as pd
import logging
from datetime import datetime

class CryptoDataFetcher:
    def __init__(self):
        # Initialize exchange (using Binance as it's reliable and free)
        self.exchange = ccxt.binance()
        
    def fetch_price(self, symbol):
        """Fetch current price for a crypto symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'change_24h_percent': ticker['percentage'],
                'volume_24h': ticker['quoteVolume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except Exception as e:
            logging.error(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    def fetch_fear_greed(self, limit=1):
        """
        Fetch Fear & Greed Index from alternative.me
        limit = number of data points (default 1 for latest)
        """
        try:
            url = f"https://api.alternative.me/fng/?limit={limit}"
            response = requests.get(url)
            data = response.json()["data"]
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
            df["value"] = df["value"].astype(int)
            return df[["timestamp", "value", "value_classification"]]
        except Exception as e:
            logging.error(f"Error fetching fear & greed index: {str(e)}")
            return None
    
    def get_crypto_summary(self, symbols):
        """Get summary of crypto prices and fear & greed index"""
        try:
            summary = {
                'prices': {},
                'fear_greed': None,
                'timestamp': datetime.now()
            }
            
            # Fetch prices for each symbol
            for symbol in symbols:
                price = self.fetch_price(symbol)
                if price:
                    summary['prices'][symbol] = price
            
            # Fetch fear & greed index
            fg_data = self.fetch_fear_greed(1)
            if fg_data is not None and not fg_data.empty:
                summary['fear_greed'] = {
                    'value': fg_data.iloc[0]['value'],
                    'classification': fg_data.iloc[0]['value_classification'],
                    'timestamp': fg_data.iloc[0]['timestamp']
                }
            
            return summary
        except Exception as e:
            logging.error(f"Error getting crypto summary: {str(e)}")
            return None
    
# # Example usage:
# if __name__ == "__main__":
#     fetcher = CryptoDataFetcher()
    
#     # For single crypto - returns flattened data
#     btc_data = fetcher.get_crypto_summary(['BTC/USDT'])
#     if btc_data and 'BTC/USDT' in btc_data['prices']:
#         btc = btc_data['prices']['BTC/USDT']
#         print("Single crypto data:")
#         print(f"Symbol: {btc['symbol']}")
#         print(f"Price: ${btc['price']:,.2f}")
#         print(f"24h Change: {btc['change_24h_percent']:+.2f}%")
#         print(f"24h Volume: ${btc['volume_24h']:,.0f}")
#         print(f"24h High: ${btc['high_24h']:,.2f}")
#         print(f"24h Low: ${btc['low_24h']:,.2f}")

#         if btc_data['fear_greed']:
#             fg = btc_data['fear_greed']
#             print(f"Fear & Greed: {fg['value']} ({fg['classification']})")

    
#     print("\n" + "-"*50 + "\n")
    
#     # For multiple cryptos - returns nested structure
#     multi_data = fetcher.get_crypto_summary(['BTC/USDT', 'ETH/USDT','TON/USDT','XRP/USDT','TRB/USDT'])
#     if multi_data:
#         print("Multiple crypto data:")
#         for symbol, data in multi_data['prices'].items():
#             print(f"{symbol}: ${data['price']:,.2f} ({data['change_24h_percent']:+.2f}%)")