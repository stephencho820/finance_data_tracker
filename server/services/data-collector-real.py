#!/usr/bin/env python3
import sys
import json
import traceback
from datetime import datetime

def collect_korean_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect Korean stock data using pykrx"""
    try:
        import pykrx.stock as stock
        from pykrx import stock as pykrx_stock
        
        # Convert string dates
        end_date_fmt = end_date.replace('-', '')
        start_date_fmt = start_date.replace('-', '')
        
        data = []
        
        # Get tickers based on market
        if market == 'kospi':
            tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KOSPI")
            market_name = "KOSPI"
        elif market == 'kosdaq':
            tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KOSDAQ")
            market_name = "KOSDAQ"
        elif market == 'konex':
            tickers = pykrx_stock.get_market_ticker_list(end_date_fmt, market="KONEX")
            market_name = "KONEX"
        elif market == 'etf':
            tickers = pykrx_stock.get_etf_ticker_list(end_date_fmt)
            market_name = "ETF"
        else:
            raise ValueError(f"Unknown Korean market: {market}")
        
        # Limit to just a few stocks for testing
        max_tickers = min(limit if limit and limit <= 5 else 3, len(tickers))
        tickers = tickers[:max_tickers]
        
        # Process each ticker
        for ticker in tickers:
            try:
                # Get stock name
                name = pykrx_stock.get_market_ticker_name(ticker)
                
                # Get OHLCV data
                ohlcv_df = pykrx_stock.get_market_ohlcv_by_date(start_date_fmt, end_date_fmt, ticker)
                
                if not ohlcv_df.empty:
                    latest = ohlcv_df.iloc[-1]
                    prev = ohlcv_df.iloc[-2] if len(ohlcv_df) > 1 else latest
                    
                    current_price = float(latest['종가'])
                    prev_price = float(prev['종가'])
                    change = current_price - prev_price
                    change_percent = (change / prev_price * 100) if prev_price != 0 else 0
                    
                    # Get market cap
                    market_cap = None
                    shares_outstanding = None
                    try:
                        cap_df = pykrx_stock.get_market_cap_by_date(end_date_fmt, end_date_fmt, ticker)
                        if not cap_df.empty:
                            market_cap = int(cap_df.iloc[0]['시가총액'])
                            shares_outstanding = int(cap_df.iloc[0]['상장주식수'])
                    except:
                        pass
                    
                    # Get fundamental data
                    pe_ratio = None
                    pbr = None
                    dividend_yield = None
                    try:
                        fund_df = pykrx_stock.get_market_fundamental_by_date(end_date_fmt, end_date_fmt, ticker)
                        if not fund_df.empty:
                            pe_ratio = fund_df.iloc[0].get('PER')
                            pbr = fund_df.iloc[0].get('PBR')
                            dividend_yield = fund_df.iloc[0].get('DIV')
                    except:
                        pass
                    
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
                    
            except Exception as e:
                # Skip individual stock errors
                continue
        
        # Sort data if requested
        if sort_by and data:
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
        raise Exception(f"Error collecting Korean data: {str(e)}")

def collect_us_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect US stock data using yfinance"""
    try:
        import yfinance as yf
        
        # Define popular tickers for each market
        if market == 'sp500':
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        elif market == 'nasdaq':
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        elif market == 'dow':
            tickers = ['AAPL', 'MSFT', 'UNH', 'GS', 'HD']
        elif market == 'russell2000':
            tickers = ['IWM', 'VTWO', 'URTY', 'TNA', 'SCHA']
        else:
            raise ValueError(f"Unknown US market: {market}")
        
        # Limit tickers
        max_tickers = min(limit if limit and limit <= 5 else 3, len(tickers))
        tickers = tickers[:max_tickers]
        
        data = []
        
        for symbol in tickers:
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
        
        # Sort data if requested
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
            'message': f'Successfully collected {len(result)} records using real API'
        }))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'message': str(e),
            'traceback': traceback.format_exc()
        }))

if __name__ == "__main__":
    main()