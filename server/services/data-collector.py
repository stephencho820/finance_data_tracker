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
        
        # For better performance, use the most recent trading day if end date is in future
        today = datetime.now()
        if end_dt > today:
            end_dt = today
        
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
        
        # Get more comprehensive data - increase limit
        tickers = tickers[:100]
        
        # Process stocks in batches for better performance
        batch_size = 20
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            
            for ticker in batch:
                try:
                    # Get comprehensive stock info
                    name = pykrx_stock.get_market_ticker_name(ticker)
                    
                    # Get OHLCV data with comprehensive info
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
                        
                        # Get comprehensive market data
                        market_cap = "N/A"
                        shares_outstanding = "N/A"
                        pe_ratio = "N/A"
                        pbr = "N/A"
                        dividend_yield = "N/A"
                        
                        try:
                            # Market capitalization and shares
                            market_cap_raw = pykrx_stock.get_market_cap_by_date(
                                end_dt.strftime('%Y%m%d'), 
                                end_dt.strftime('%Y%m%d'), 
                                ticker
                            )
                            if not market_cap_raw.empty:
                                cap_value = market_cap_raw.iloc[0]['시가총액']
                                shares_value = market_cap_raw.iloc[0]['상장주식수']
                                
                                if cap_value > 1e12:
                                    market_cap = f"{cap_value/1e12:.1f}조원"
                                elif cap_value > 1e8:
                                    market_cap = f"{cap_value/1e8:.0f}억원"
                                
                                if shares_value > 1e8:
                                    shares_outstanding = f"{shares_value/1e8:.0f}억주"
                                elif shares_value > 1e4:
                                    shares_outstanding = f"{shares_value/1e4:.0f}만주"
                        except:
                            pass
                        
                        try:
                            # Get fundamental data (PER, PBR, etc.)
                            fundamental_raw = pykrx_stock.get_market_fundamental_by_date(
                                end_dt.strftime('%Y%m%d'), 
                                end_dt.strftime('%Y%m%d'), 
                                ticker
                            )
                            if not fundamental_raw.empty:
                                fund_data = fundamental_raw.iloc[0]
                                pe_ratio = fund_data.get('PER', 'N/A')
                                pbr = fund_data.get('PBR', 'N/A')
                                dividend_yield = fund_data.get('DIV', 'N/A')
                                
                                # Format dividend yield as percentage
                                if dividend_yield != 'N/A' and dividend_yield > 0:
                                    dividend_yield = f"{dividend_yield:.2f}%"
                        except:
                            pass
                        
                        # Get trading value info
                        trading_value = "N/A"
                        try:
                            trading_value_raw = latest.get('거래대금', 0)
                            if trading_value_raw > 1e8:
                                trading_value = f"{trading_value_raw/1e8:.0f}억원"
                            elif trading_value_raw > 1e4:
                                trading_value = f"{trading_value_raw/1e4:.0f}만원"
                        except:
                            pass
                        
                        # Get 52-week high/low from historical data
                        week_52_high = "N/A"
                        week_52_low = "N/A"
                        try:
                            # Get 1 year of data for 52-week calculation
                            year_ago = (end_dt - timedelta(days=365)).strftime('%Y%m%d')
                            year_df = pykrx_stock.get_market_ohlcv_by_date(year_ago, 
                                                                          end_dt.strftime('%Y%m%d'), 
                                                                          ticker)
                            if not year_df.empty:
                                week_52_high = float(year_df['고가'].max())
                                week_52_low = float(year_df['저가'].min())
                        except:
                            pass
                        
                        data.append({
                            'symbol': ticker,
                            'name': name,
                            'price': float(current_price),
                            'change': float(change),
                            'changePercent': float(change_percent),
                            'volume': int(latest['거래량']),
                            'marketCap': market_cap,
                            'peRatio': pe_ratio if pe_ratio != 'N/A' else None,
                            'pbr': pbr if pbr != 'N/A' else None,
                            'dividendYield': dividend_yield,
                            'week52High': week_52_high if week_52_high != 'N/A' else None,
                            'week52Low': week_52_low if week_52_low != 'N/A' else None,
                            'sharesOutstanding': shares_outstanding,
                            'tradingValue': trading_value,
                            'openPrice': float(latest['시가']),
                            'highPrice': float(latest['고가']),
                            'lowPrice': float(latest['저가']),
                            'country': 'korea',
                            'market': market_name,
                            'date': end_date
                        })
                        
                except Exception as e:
                    # Skip individual stock errors but continue processing
                    continue
            
            # Add a small delay between batches to avoid overwhelming the API
            import time
            time.sleep(0.1)
                
        return data
        
    except Exception as e:
        raise Exception(f"Error collecting Korean data: {str(e)}")

def collect_us_data(start_date, end_date, market):
    """Collect US stock data using yfinance"""
    try:
        import yfinance as yf
        
        data = []
        
        # Define comprehensive market symbols
        market_symbols = {
            'sp500': ['^GSPC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH', 
                     'JNJ', 'V', 'PG', 'JPM', 'HD', 'MA', 'AVGO', 'CVX', 'LLY', 'PFE', 'ABBV', 'KO', 
                     'PEP', 'TMO', 'MRK', 'COST', 'WMT', 'ACN', 'DHR', 'NEE', 'VZ', 'ABT', 'ADBE', 
                     'CRM', 'TXN', 'NKE', 'QCOM', 'T', 'AMD', 'NFLX', 'RTX', 'BMY', 'UPS', 'LOW', 
                     'HON', 'ORCL', 'MDT', 'IBM', 'AMT', 'SPGI'],
            'nasdaq': ['^IXIC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE',
                      'PYPL', 'INTC', 'CMCSA', 'CSCO', 'AVGO', 'TXN', 'QCOM', 'AMD', 'INTU', 'ISRG',
                      'BKNG', 'GILD', 'MU', 'ADI', 'AMAT', 'LRCX', 'MDLZ', 'REGN', 'ATVI', 'FISV',
                      'CSX', 'ADP', 'NXPI', 'KLAC', 'MRVL', 'ORLY', 'DXCM', 'LULU', 'EXC', 'XEL'],
            'dow': ['^DJI', 'AAPL', 'MSFT', 'UNH', 'GS', 'HD', 'CAT', 'AMGN', 'CRM', 'V', 'HON', 'IBM',
                   'BA', 'JPM', 'JNJ', 'WMT', 'PG', 'CVX', 'MRK', 'AXP', 'TRV', 'NKE', 'KO', 'MCD',
                   'MMM', 'DIS', 'DOW', 'WBA', 'INTC', 'VZ'],
            'russell': ['^RUT', 'GME', 'AMC', 'PLTR', 'BB', 'CLOV', 'WKHS', 'RIDE', 'SPCE', 'CLNE',
                       'WISH', 'SOFI', 'HOOD', 'LCID', 'RIVN', 'CLOV', 'SKLZ', 'RBLX', 'COIN', 'ROKU',
                       'BYND', 'PTON', 'ZM', 'DOCU', 'SNOW', 'CRWD', 'NET', 'DDOG', 'OKTA', 'TWLO']
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
                    
                    # Get comprehensive info
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
                    
                    # Get additional financial metrics
                    pe_ratio = info.get('trailingPE', 'N/A')
                    dividend_yield = info.get('dividendYield', 'N/A')
                    if isinstance(dividend_yield, (int, float)):
                        dividend_yield = f"{dividend_yield*100:.2f}%"
                    
                    # Get 52-week high/low
                    week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
                    week_52_low = info.get('fiftyTwoWeekLow', 'N/A')
                    
                    # Get sector and industry
                    sector = info.get('sector', 'N/A')
                    industry = info.get('industry', 'N/A')
                    
                    # Get beta (volatility measure)
                    beta = info.get('beta', 'N/A')
                    
                    # Get earnings per share
                    eps = info.get('trailingEps', 'N/A')
                    
                    data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': float(current_price),
                        'change': float(change),
                        'changePercent': float(change_percent),
                        'volume': int(latest['Volume']),
                        'marketCap': market_cap,
                        'peRatio': pe_ratio if pe_ratio != 'N/A' else 'N/A',
                        'dividendYield': dividend_yield,
                        'week52High': week_52_high if week_52_high != 'N/A' else 'N/A',
                        'week52Low': week_52_low if week_52_low != 'N/A' else 'N/A',
                        'sector': sector,
                        'industry': industry,
                        'beta': beta if beta != 'N/A' else 'N/A',
                        'eps': eps if eps != 'N/A' else 'N/A',
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
