#!/usr/bin/env python3
import sys
import json
import traceback
from datetime import datetime
import time

def collect_korean_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect Korean stock data using pykrx - Fast version"""
    try:
        import pykrx.stock as stock
        from pykrx import stock as pykrx_stock
        
        # Convert dates
        end_date_fmt = end_date.replace('-', '')
        start_date_fmt = start_date.replace('-', '')
        
        print(f"[INFO] Starting data collection for {market} market...", file=sys.stderr)
        
        data = []
        
        # Get tickers based on market selection
        if market == 'kospi':
            all_tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KOSPI")
            market_name = "KOSPI"
        elif market == 'kosdaq':
            all_tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KOSDAQ")
            market_name = "KOSDAQ"
        elif market == 'konex':
            all_tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KONEX")
            market_name = "KONEX"
        elif market == 'etf':
            all_tickers = pykrx_stock.get_etf_ticker_list(end_date_fmt)
            market_name = "ETF"
        else:
            # Default to KOSPI if unknown market
            all_tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KOSPI")
            market_name = "KOSPI"
        
        print(f"[INFO] Found {len(all_tickers)} tickers in {market_name}", file=sys.stderr)
        
        # Apply user-specified limit
        max_tickers = min(limit if limit and limit <= 50 else 10, len(all_tickers))
        selected_tickers = all_tickers[:max_tickers]
        
        print(f"[INFO] Processing {len(selected_tickers)} tickers...", file=sys.stderr)
        
        # Process each ticker with timeout
        for i, ticker in enumerate(selected_tickers):
            try:
                print(f"[INFO] Processing ticker {i+1}/{len(selected_tickers)}: {ticker}", file=sys.stderr)
                
                # Get stock name
                try:
                    name = pykrx_stock.get_market_ticker_name(ticker)
                except:
                    name = ticker
                
                # Get price data with retry
                ohlcv_df = None
                for attempt in range(2):
                    try:
                        ohlcv_df = pykrx_stock.get_market_ohlcv_by_date(start_date_fmt, end_date_fmt, ticker)
                        if not ohlcv_df.empty:
                            break
                        time.sleep(1)
                    except Exception as e:
                        print(f"[WARNING] Attempt {attempt+1} failed for {ticker}: {e}", file=sys.stderr)
                        time.sleep(2)
                
                if ohlcv_df is None or ohlcv_df.empty:
                    print(f"[WARNING] No data found for {ticker}", file=sys.stderr)
                    continue
                
                latest = ohlcv_df.iloc[-1]
                prev = ohlcv_df.iloc[-2] if len(ohlcv_df) > 1 else latest
                
                current_price = float(latest['종가'])
                prev_price = float(prev['종가'])
                change = current_price - prev_price
                change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                
                # Get additional data with error handling
                market_cap = None
                shares_outstanding = None
                pe_ratio = None
                pbr = None
                dividend_yield = None
                
                # Try to get market cap
                try:
                    cap_df = pykrx_stock.get_market_cap_by_date(end_date_fmt, end_date_fmt, ticker)
                    if not cap_df.empty:
                        market_cap = int(cap_df.iloc[0]['시가총액'])
                        shares_outstanding = int(cap_df.iloc[0]['상장주식수'])
                except Exception as e:
                    print(f"[WARNING] Failed to get market cap for {ticker}: {e}", file=sys.stderr)
                
                # Try to get fundamentals
                try:
                    fund_df = pykrx_stock.get_market_fundamental_by_date(end_date_fmt, end_date_fmt, ticker)
                    if not fund_df.empty:
                        pe_ratio = fund_df.iloc[0].get('PER')
                        pbr = fund_df.iloc[0].get('PBR')
                        dividend_yield = fund_df.iloc[0].get('DIV')
                except Exception as e:
                    print(f"[WARNING] Failed to get fundamentals for {ticker}: {e}", file=sys.stderr)
                
                data.append({
                    'symbol': ticker,
                    'name': name,
                    'current_price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'volume': int(latest['거래량']),
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'pbr': pbr,
                    'dividend_yield': dividend_yield,
                    'week_52_high': float(ohlcv_df['고가'].max()),
                    'week_52_low': float(ohlcv_df['저가'].min()),
                    'shares_outstanding': shares_outstanding,
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
                
                print(f"[INFO] Successfully processed {ticker}: {name}", file=sys.stderr)
                
            except Exception as e:
                print(f"[ERROR] Error processing {ticker}: {e}", file=sys.stderr)
                continue
        
        print(f"[INFO] Collected {len(data)} records", file=sys.stderr)
        
        # First, get additional data for sorting if needed
        if sort_by and sort_by in ['market_cap', 'pe_ratio', 'pbr'] and data:
            print(f"[INFO] Getting additional data for sorting by {sort_by}", file=sys.stderr)
            
            for i, item in enumerate(data):
                ticker = item['symbol']
                try:
                    # Get market cap and fundamentals for sorting
                    if sort_by == 'market_cap' and not item.get('market_cap'):
                        try:
                            cap_df = pykrx_stock.get_market_cap_by_date(end_date_fmt, end_date_fmt, ticker)
                            if not cap_df.empty:
                                item['market_cap'] = int(cap_df.iloc[0]['시가총액'])
                                item['shares_outstanding'] = int(cap_df.iloc[0]['상장주식수'])
                        except:
                            item['market_cap'] = 0
                    
                    if sort_by in ['pe_ratio', 'pbr'] and not item.get(sort_by):
                        try:
                            fund_df = pykrx_stock.get_market_fundamental_by_date(end_date_fmt, end_date_fmt, ticker)
                            if not fund_df.empty:
                                if sort_by == 'pe_ratio':
                                    item['pe_ratio'] = fund_df.iloc[0].get('PER')
                                elif sort_by == 'pbr':
                                    item['pbr'] = fund_df.iloc[0].get('PBR')
                                item['dividend_yield'] = fund_df.iloc[0].get('DIV')
                        except:
                            pass
                    
                    if i % 10 == 0:  # Progress update every 10 items
                        print(f"[INFO] Processed {i+1}/{len(data)} items for sorting", file=sys.stderr)
                        
                except Exception as e:
                    print(f"[WARNING] Error getting additional data for {ticker}: {e}", file=sys.stderr)
                    continue
        
        # Sort data based on user selection
        if sort_by and data:
            print(f"[INFO] Sorting data by {sort_by}", file=sys.stderr)
            if sort_by == 'market_cap':
                data.sort(key=lambda x: x.get('market_cap', 0) or 0, reverse=True)
            elif sort_by == 'current_price':
                data.sort(key=lambda x: x.get('current_price', 0), reverse=True)
            elif sort_by == 'pe_ratio':
                data.sort(key=lambda x: x.get('pe_ratio', 0) or float('inf'), reverse=False)
            elif sort_by == 'pbr':
                data.sort(key=lambda x: x.get('pbr', 0) or float('inf'), reverse=False)
            elif sort_by == 'dividend_yield':
                data.sort(key=lambda x: x.get('dividend_yield', 0) or 0, reverse=True)
            elif sort_by == 'volume':
                data.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
        return data
        
    except Exception as e:
        print(f"[ERROR] Error in collect_korean_data: {e}", file=sys.stderr)
        raise Exception(f"Error collecting Korean data: {str(e)}")

def collect_us_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect US stock data using yfinance"""
    try:
        import yfinance as yf
        
        # Define comprehensive tickers for each market
        if market == 'sp500':
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'V', 'JNJ', 
                      'WMT', 'JPM', 'PG', 'UNH', 'HD', 'CVX', 'MA', 'PFE', 'BAC', 'ABBV', 'KO', 'AVGO',
                      'PEP', 'COST', 'TMO', 'DHR', 'ABT', 'VZ', 'ADBE', 'NKE', 'CRM', 'LLY', 'CMCSA',
                      'NFLX', 'INTC', 'T', 'AMD', 'TXN', 'QCOM', 'NEE', 'HON', 'PM', 'UNP', 'IBM', 'RTX',
                      'LOW', 'SPGI', 'INTU', 'GS', 'CAT', 'AMGN', 'ISRG', 'BKNG', 'DE', 'AXP', 'MDLZ',
                      'BLK', 'GILD', 'MU', 'TJX', 'SCHW', 'CVS', 'LRCX', 'TMUS', 'ADP', 'VRTX', 'REGN',
                      'ZTS', 'PYPL', 'CHTR', 'AMAT', 'MMM', 'SYK', 'EOG', 'EQIX', 'BSX', 'KLAC', 'DUK',
                      'PLD', 'SO', 'MO', 'ICE', 'ATVI', 'ITW', 'CME', 'WM', 'NOC', 'APD', 'TFC', 'ECL',
                      'SHW', 'MMC', 'FDX', 'GD', 'NSC', 'USB', 'CL', 'AON', 'BIIB', 'BDX', 'CSX', 'MCO']
        elif market == 'nasdaq':
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AVGO', 'NFLX', 'ADBE',
                      'CRM', 'PYPL', 'INTC', 'CMCSA', 'PEP', 'COST', 'CSCO', 'TXN', 'QCOM', 'AMGN',
                      'INTU', 'ISRG', 'BKNG', 'MU', 'GILD', 'REGN', 'VRTX', 'LRCX', 'AMAT', 'KLAC',
                      'ATVI', 'CHTR', 'MELI', 'MRVL', 'ORLY', 'CTAS', 'NTES', 'WDAY', 'FAST', 'PAYX',
                      'VRSK', 'EBAY', 'MNST', 'CTSH', 'DXCM', 'SPLK', 'ROST', 'PCAR', 'SNPS', 'CDNS']
        elif market == 'dow':
            tickers = ['AAPL', 'MSFT', 'UNH', 'GS', 'HD', 'CAT', 'AMGN', 'MCD', 'V', 'BA', 'CRM',
                      'TRV', 'AXP', 'JPM', 'JNJ', 'WMT', 'CVX', 'NKE', 'PG', 'IBM', 'MMM', 'DIS',
                      'MRK', 'KO', 'HON', 'VZ', 'CSCO', 'WBA', 'DOW', 'INTC']
        elif market == 'russell2000':
            tickers = ['IWM', 'VTWO', 'URTY', 'TNA', 'SCHA', 'VTI', 'ITOT', 'SPTM', 'SCHB', 'VEA',
                      'SPYG', 'SPYV', 'VTV', 'VUG', 'VMOT', 'VTEB', 'VXUS', 'VT', 'VTIAX', 'VTSAX',
                      'VTISX', 'VTWSX', 'VGTSX', 'VGSLX', 'VGSTX', 'VEURX', 'VPADX', 'VWELX', 'VWINX',
                      'VWUSX', 'VFICX', 'VUSTX', 'VUSUX', 'VSGDX', 'VSGIX', 'VSIGX', 'VSIIX', 'VSCIX',
                      'VSCGX', 'VSCVX', 'VSMAX', 'VSMGX', 'VSMVX', 'VSMLX', 'VSMCX', 'VSMIX', 'VSMKX']
        else:
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'V', 'JNJ']
        
        # Apply user-specified limit
        max_tickers = min(limit if limit and limit <= 50 else 10, len(tickers))
        selected_tickers = tickers[:max_tickers]
        
        data = []
        
        for symbol in selected_tickers:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    
                    current_price = latest['Close']
                    prev_price = prev['Close']
                    change = current_price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                    
                    info = ticker.info
                    name = info.get('longName', info.get('shortName', symbol))
                    
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
                        'week_52_high': round(hist['High'].max(), 2),
                        'week_52_low': round(hist['Low'].min(), 2),
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
                continue
        
        # Sort data based on user selection
        if sort_by and data:
            if sort_by == 'market_cap':
                data.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
            elif sort_by == 'current_price':
                data.sort(key=lambda x: x.get('current_price', 0), reverse=True)
            elif sort_by == 'pe_ratio':
                data.sort(key=lambda x: x.get('pe_ratio', 0) if x.get('pe_ratio', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'pbr':
                data.sort(key=lambda x: x.get('pbr', 0) if x.get('pbr', 0) != 0 else float('inf'), reverse=False)
            elif sort_by == 'dividend_yield':
                data.sort(key=lambda x: x.get('dividend_yield', 0), reverse=True)
            elif sort_by == 'volume':
                data.sort(key=lambda x: x.get('volume', 0), reverse=True)
        
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
        
        print(f"[INFO] Starting data collection for {country} {market}", file=sys.stderr)
        
        if country == 'korea':
            result = collect_korean_data(start_date, end_date, market, sort_by, limit)
        elif country == 'usa':
            result = collect_us_data(start_date, end_date, market, sort_by, limit)
        else:
            raise ValueError(f"Unknown country: {country}")
        
        # Apply limit if specified
        if limit and len(result) > limit:
            result = result[:limit]
        
        print(json.dumps({
            'success': True,
            'data': result,
            'message': f'Successfully collected {len(result)} records using REAL pykrx API'
        }))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'message': f'Real API error: {str(e)}',
            'traceback': traceback.format_exc()
        }))

if __name__ == "__main__":
    main()