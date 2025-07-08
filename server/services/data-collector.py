#!/usr/bin/env python3
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import traceback

def collect_korean_data(start_date, end_date, market):
    """Collect Korean stock data using pykrx"""
    try:
        import pykrx.stock as stock
        from pykrx import stock as pykrx_stock
        
        # Convert string dates to datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        data = []
        
        if market == 'kospi':
            # Get KOSPI listed companies
            tickers = pykrx_stock.get_market_ticker_list(market="KOSPI")
            market_name = "KOSPI"
        elif market == 'kosdaq':
            # Get KOSDAQ listed companies
            tickers = pykrx_stock.get_market_ticker_list(market="KOSDAQ")
            market_name = "KOSDAQ"
        elif market == 'konex':
            # Get KONEX listed companies
            tickers = pykrx_stock.get_market_ticker_list(market="KONEX")
            market_name = "KONEX"
        elif market == 'etf':
            # Get ETF listed
            tickers = pykrx_stock.get_etf_ticker_list()
            market_name = "ETF"
        else:
            raise ValueError(f"Unknown Korean market: {market}")
        
        # Limit to top 10 for performance and speed
        tickers = tickers[:10]
        
        for ticker in tickers:
            try:
                # Get stock info
                name = pykrx_stock.get_market_ticker_name(ticker)
                
                # Get recent price data
                df = pykrx_stock.get_market_ohlcv_by_date(start_dt.strftime('%Y%m%d'), 
                                                        end_dt.strftime('%Y%m%d'), 
                                                        ticker)
                
                if not df.empty:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2] if len(df) > 1 else latest
                    
                    current_price = latest['종가']
                    prev_price = prev['종가']
                    change = current_price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                    
                    # Get market cap (approximate)
                    market_cap_raw = pykrx_stock.get_market_cap_by_date(
                        end_dt.strftime('%Y%m%d'), 
                        end_dt.strftime('%Y%m%d'), 
                        ticker
                    )
                    
                    market_cap = "N/A"
                    if not market_cap_raw.empty:
                        cap_value = market_cap_raw.iloc[0]['시가총액']
                        market_cap = f"{cap_value/1e12:.1f}조원"
                    
                    data.append({
                        'symbol': ticker,
                        'name': name,
                        'price': float(current_price),
                        'change': float(change),
                        'changePercent': float(change_percent),
                        'volume': int(latest['거래량']),
                        'marketCap': market_cap,
                        'country': 'korea',
                        'market': market_name,
                        'date': end_date
                    })
                    
            except Exception as e:
                # Skip individual stock errors
                continue
                
        return data
        
    except Exception as e:
        raise Exception(f"Error collecting Korean data: {str(e)}")

def collect_us_data(start_date, end_date, market):
    """Collect US stock data using yfinance"""
    try:
        import yfinance as yf
        
        data = []
        
        # Define market symbols
        market_symbols = {
            'sp500': ['^GSPC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH'],
            'nasdaq': ['^IXIC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE'],
            'dow': ['^DJI', 'AAPL', 'MSFT', 'UNH', 'GS', 'HD', 'CAT', 'AMGN', 'CRM', 'V'],
            'russell': ['^RUT', 'GME', 'AMC', 'PLTR', 'WISH', 'CLOV', 'BB', 'CLNE', 'WKHS', 'RIDE']
        }
        
        if market not in market_symbols:
            raise ValueError(f"Unknown US market: {market}")
        
        symbols = market_symbols[market]
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Get historical data
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    current_price = latest['Close']
                    prev_price = prev['Close']
                    change = current_price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                    
                    # Get basic info
                    info = ticker.info
                    name = info.get('longName', info.get('shortName', symbol))
                    
                    # Market cap
                    market_cap = "N/A"
                    if 'marketCap' in info and info['marketCap']:
                        cap_value = info['marketCap']
                        if cap_value > 1e12:
                            market_cap = f"${cap_value/1e12:.1f}T"
                        elif cap_value > 1e9:
                            market_cap = f"${cap_value/1e9:.1f}B"
                        elif cap_value > 1e6:
                            market_cap = f"${cap_value/1e6:.1f}M"
                    
                    data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': float(current_price),
                        'change': float(change),
                        'changePercent': float(change_percent),
                        'volume': int(latest['Volume']),
                        'marketCap': market_cap,
                        'country': 'usa',
                        'market': market.upper(),
                        'date': end_date
                    })
                    
            except Exception as e:
                # Skip individual stock errors
                continue
                
        return data
        
    except Exception as e:
        raise Exception(f"Error collecting US data: {str(e)}")

def main():
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        
        start_date = input_data['startDate']
        end_date = input_data['endDate']
        country = input_data['country']
        market = input_data['market']
        
        if country == 'korea':
            data = collect_korean_data(start_date, end_date, market)
        elif country == 'usa':
            data = collect_us_data(start_date, end_date, market)
        else:
            raise ValueError(f"Unknown country: {country}")
        
        # Output result
        result = {
            'success': True,
            'data': data,
            'message': f'Successfully collected {len(data)} records'
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        # Output error
        result = {
            'success': False,
            'data': [],
            'message': str(e),
            'traceback': traceback.format_exc()
        }
        
        print(json.dumps(result))
        sys.exit(1)

if __name__ == "__main__":
    main()
