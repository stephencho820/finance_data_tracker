#!/usr/bin/env python3
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
import traceback

def collect_korean_data(start_date, end_date, market, sort_by=None, limit=None):
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
        
        # Apply custom limit or use default for performance
        max_tickers = limit if limit and limit <= 20 else 5
        tickers = tickers[:max_tickers]
        
        # Process stocks in smaller batches for better performance
        batch_size = 5
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
                        
                        # Get 52-week high/low from recent data only (for performance)
                        week_52_high = "N/A"
                        week_52_low = "N/A"
                        try:
                            # Use current data for high/low approximation
                            if not df.empty:
                                week_52_high = float(df['고가'].max())
                                week_52_low = float(df['저가'].min())
                        except:
                            pass
                        
                        data.append({
                            'symbol': ticker,
                            'name': name,
                            'current_price': float(current_price),
                            'change': float(change),
                            'change_percent': float(change_percent),
                            'volume': int(latest['거래량']),
                            'market_cap': int(market_cap_raw.iloc[0]['시가총액']) if not market_cap_raw.empty else None,
                            'pe_ratio': pe_ratio if pe_ratio != 'N/A' else None,
                            'pbr': pbr if pbr != 'N/A' else None,
                            'dividend_yield': dividend_yield,
                            'week_52_high': week_52_high if week_52_high != 'N/A' else None,
                            'week_52_low': week_52_low if week_52_low != 'N/A' else None,
                            'shares_outstanding': int(market_cap_raw.iloc[0]['상장주식수']) if not market_cap_raw.empty else None,
                            'eps': None,
                            'sector': None,
                            'industry': None,
                            'beta': None,
                            'book_value': None,
                            'revenue': None,
                            'net_income': None,
                            'debt_to_equity': None,
                            'roe': None,
                            'roa': None,
                            'operating_margin': None,
                            'profit_margin': None,
                            'revenue_growth': None,
                            'earnings_growth': None,
                            'current_ratio': None,
                            'quick_ratio': None,
                            'price_to_sales': None,
                            'price_to_cash_flow': None,
                            'enterprise_value': None,
                            'ev_to_revenue': None,
                            'ev_to_ebitda': None,
                            'free_cash_flow': None,
                            'country': 'Korea',
                            'market': market_name,
                            'date': end_date
                        })
                        
                except Exception as e:
                    # Skip individual stock errors but continue processing
                    continue
            
            # Add delay between batches to avoid overwhelming the API
            import time
            time.sleep(0.5)
        
        # Sort data by specified criteria
        if sort_by and data:
            reverse_sort = True  # Default to descending order for most financial metrics
            if sort_by == 'current_price':
                data.sort(key=lambda x: x.get('current_price', 0), reverse=reverse_sort)
            elif sort_by == 'market_cap':
                data.sort(key=lambda x: x.get('market_cap', 0), reverse=reverse_sort)
            elif sort_by == 'pe_ratio':
                data.sort(key=lambda x: x.get('pe_ratio', 0) if x.get('pe_ratio', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'pbr':
                data.sort(key=lambda x: x.get('pbr', 0) if x.get('pbr', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'dividend_yield':
                data.sort(key=lambda x: x.get('dividend_yield', 0), reverse=reverse_sort)
            elif sort_by == 'volume':
                data.sort(key=lambda x: x.get('volume', 0), reverse=reverse_sort)
                
        return data
        
    except Exception as e:
        raise Exception(f"Error collecting Korean data: {str(e)}")

def collect_us_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect US stock data using yfinance"""
    try:
        import yfinance as yf
        
        data = []
        
        # Optimized market symbols for performance
        market_symbols = {
            'sp500': ['^GSPC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B', 'UNH', 
                     'JNJ', 'V', 'PG', 'JPM', 'HD', 'MA', 'AVGO', 'CVX', 'LLY', 'PFE'],
            'nasdaq': ['^IXIC', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE',
                      'PYPL', 'INTC', 'CMCSA', 'CSCO', 'AVGO', 'TXN', 'QCOM', 'AMD', 'INTU', 'ISRG'],
            'dow': ['^DJI', 'AAPL', 'MSFT', 'UNH', 'GS', 'HD', 'CAT', 'AMGN', 'CRM', 'V', 'HON', 'IBM',
                   'BA', 'JPM', 'JNJ', 'WMT', 'PG', 'CVX', 'MRK', 'AXP'],
            'russell': ['^RUT', 'GME', 'AMC', 'PLTR', 'BB', 'CLOV', 'WKHS', 'RIDE', 'SPCE', 'CLNE',
                       'WISH', 'SOFI', 'HOOD', 'LCID', 'RIVN', 'SKLZ', 'RBLX', 'COIN', 'ROKU', 'BYND']
        }
        
        if market not in market_symbols:
            raise ValueError(f"Unknown US market: {market}")
        
        symbols = market_symbols[market]
        
        # Apply custom limit or use default for performance
        max_symbols = limit if limit and limit <= 50 else 10
        symbols = symbols[:max_symbols]
        
        # Process symbols in smaller batches for better performance
        batch_size = 5
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            for symbol in batch:
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
                        
                        # Use available data from history for 52-week high/low
                        week_52_high = hist['High'].max()
                        week_52_low = hist['Low'].min()
                        
                        data.append({
                            'symbol': symbol,
                            'name': name,
                            'current_price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': int(latest['Volume']) if latest['Volume'] else 0,
                            'market_cap': info.get('marketCap', 0),
                            'pe_ratio': info.get('forwardPE', info.get('trailingPE', 0)),
                            'pbr': info.get('priceToBook', 0),
                            'eps': info.get('trailingEps', 0),
                            'dividend_yield': info.get('dividendYield', 0),
                            'week_52_high': round(week_52_high, 2) if week_52_high else 0,
                            'week_52_low': round(week_52_low, 2) if week_52_low else 0,
                            'beta': info.get('beta', 0),
                            'shares_outstanding': info.get('sharesOutstanding', 0),
                            'book_value': info.get('bookValue', 0),
                            'revenue': info.get('totalRevenue', 0),
                            'net_income': info.get('netIncomeToCommon', 0),
                            'debt_to_equity': info.get('debtToEquity', 0),
                            'roe': info.get('returnOnEquity', 0),
                            'roa': info.get('returnOnAssets', 0),
                            'operating_margin': info.get('operatingMargins', 0),
                            'profit_margin': info.get('profitMargins', 0),
                            'revenue_growth': info.get('revenueGrowth', 0),
                            'earnings_growth': info.get('earningsGrowth', 0),
                            'current_ratio': info.get('currentRatio', 0),
                            'quick_ratio': info.get('quickRatio', 0),
                            'price_to_sales': info.get('priceToSalesTrailing12Months', 0),
                            'price_to_cash_flow': info.get('priceToFreeCashflow', 0),
                            'enterprise_value': info.get('enterpriseValue', 0),
                            'ev_to_revenue': info.get('enterpriseToRevenue', 0),
                            'ev_to_ebitda': info.get('enterpriseToEbitda', 0),
                            'free_cash_flow': info.get('freeCashflow', 0),
                            'sector': info.get('sector', ''),
                            'industry': info.get('industry', ''),
                            'country': 'USA',
                            'market': market.upper(),
                            'date': end_date
                        })
                        
                except Exception as e:
                    # Skip individual stock errors but continue processing
                    continue
            
            # Add delay between batches to avoid rate limiting
            import time
            time.sleep(0.5)
        
        # Sort data by specified criteria
        if sort_by and data:
            reverse_sort = True  # Default to descending order for most financial metrics
            if sort_by == 'current_price':
                data.sort(key=lambda x: x.get('current_price', 0), reverse=reverse_sort)
            elif sort_by == 'market_cap':
                data.sort(key=lambda x: x.get('market_cap', 0), reverse=reverse_sort)
            elif sort_by == 'pe_ratio':
                data.sort(key=lambda x: x.get('pe_ratio', 0) if x.get('pe_ratio', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'pbr':
                data.sort(key=lambda x: x.get('pbr', 0) if x.get('pbr', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'dividend_yield':
                data.sort(key=lambda x: x.get('dividend_yield', 0), reverse=reverse_sort)
            elif sort_by == 'volume':
                data.sort(key=lambda x: x.get('volume', 0), reverse=reverse_sort)
                
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
        sort_by = input_data.get('sortBy')
        limit = input_data.get('limit')
        
        if country == 'korea':
            data = collect_korean_data(start_date, end_date, market, sort_by, limit)
        elif country == 'usa':
            data = collect_us_data(start_date, end_date, market, sort_by, limit)
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
