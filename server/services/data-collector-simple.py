#!/usr/bin/env python3
import sys
import json
import traceback
from datetime import datetime

def collect_korean_data(start_date, end_date, market):
    """Collect sample Korean stock data"""
    
    # Sample Korean data
    korean_stocks = {
        'kospi': [
            {'symbol': '005930', 'name': '삼성전자', 'price': 71000, 'change': 1000, 'changePercent': 1.43, 'volume': 12345678, 'marketCap': '421조원'},
            {'symbol': '000660', 'name': 'SK하이닉스', 'price': 128000, 'change': -2000, 'changePercent': -1.54, 'volume': 5678901, 'marketCap': '93조원'},
            {'symbol': '207940', 'name': '삼성바이오로직스', 'price': 820000, 'change': 15000, 'changePercent': 1.86, 'volume': 234567, 'marketCap': '120조원'},
            {'symbol': '005380', 'name': '현대차', 'price': 240000, 'change': 5000, 'changePercent': 2.13, 'volume': 1234567, 'marketCap': '51조원'},
            {'symbol': '051910', 'name': 'LG화학', 'price': 450000, 'change': -8000, 'changePercent': -1.75, 'volume': 567890, 'marketCap': '32조원'},
        ],
        'kosdaq': [
            {'symbol': '066570', 'name': 'LG전자', 'price': 85000, 'change': 2000, 'changePercent': 2.41, 'volume': 2345678, 'marketCap': '21조원'},
            {'symbol': '035420', 'name': 'NAVER', 'price': 180000, 'change': -3000, 'changePercent': -1.64, 'volume': 1234567, 'marketCap': '30조원'},
            {'symbol': '035720', 'name': '카카오', 'price': 55000, 'change': 1500, 'changePercent': 2.8, 'volume': 3456789, 'marketCap': '24조원'},
            {'symbol': '003550', 'name': 'LG', 'price': 92000, 'change': -1000, 'changePercent': -1.08, 'volume': 876543, 'marketCap': '11조원'},
            {'symbol': '096770', 'name': 'SK이노베이션', 'price': 150000, 'change': 3000, 'changePercent': 2.04, 'volume': 654321, 'marketCap': '16조원'},
        ],
        'konex': [
            {'symbol': '068270', 'name': '셀트리온', 'price': 180000, 'change': 4000, 'changePercent': 2.27, 'volume': 543210, 'marketCap': '24조원'},
            {'symbol': '028260', 'name': '삼성물산', 'price': 125000, 'change': -1500, 'changePercent': -1.19, 'volume': 432109, 'marketCap': '15조원'},
            {'symbol': '009150', 'name': '삼성전기', 'price': 160000, 'change': 2500, 'changePercent': 1.59, 'volume': 321098, 'marketCap': '11조원'},
        ],
        'etf': [
            {'symbol': '069500', 'name': 'KODEX 200', 'price': 35000, 'change': 200, 'changePercent': 0.57, 'volume': 9876543, 'marketCap': '8조원'},
            {'symbol': '114800', 'name': 'KODEX 인버스', 'price': 4500, 'change': -50, 'changePercent': -1.1, 'volume': 2345678, 'marketCap': '1조원'},
            {'symbol': '122630', 'name': 'KODEX 레버리지', 'price': 15000, 'change': 300, 'changePercent': 2.04, 'volume': 1876543, 'marketCap': '3조원'},
        ]
    }
    
    data = []
    stocks = korean_stocks.get(market, [])
    
    for stock in stocks:
        data.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'price': float(stock['price']),
            'change': float(stock['change']),
            'changePercent': float(stock['changePercent']),
            'volume': int(stock['volume']),
            'marketCap': stock['marketCap'],
            'country': 'korea',
            'market': market.upper(),
            'date': end_date
        })
    
    return data

def collect_us_data(start_date, end_date, market):
    """Collect sample US stock data"""
    
    # Sample US data
    us_stocks = {
        'sp500': [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 193.50, 'change': 2.45, 'changePercent': 1.28, 'volume': 45678901, 'marketCap': '$3.0T'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'price': 415.30, 'change': -3.20, 'changePercent': -0.76, 'volume': 28945673, 'marketCap': '$3.1T'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'price': 142.80, 'change': 1.75, 'changePercent': 1.24, 'volume': 23456789, 'marketCap': '$1.8T'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'price': 145.60, 'change': -0.85, 'changePercent': -0.58, 'volume': 34567890, 'marketCap': '$1.5T'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'price': 248.50, 'change': 8.20, 'changePercent': 3.41, 'volume': 78901234, 'marketCap': '$787.4B'},
        ],
        'nasdaq': [
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'price': 875.30, 'change': 15.60, 'changePercent': 1.82, 'volume': 56789012, 'marketCap': '$2.1T'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'price': 498.20, 'change': -7.40, 'changePercent': -1.46, 'volume': 23456789, 'marketCap': '$1.3T'},
            {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'price': 642.80, 'change': 12.30, 'changePercent': 1.95, 'volume': 12345678, 'marketCap': '$286.5B'},
            {'symbol': 'ADBE', 'name': 'Adobe Inc.', 'price': 556.40, 'change': -4.60, 'changePercent': -0.82, 'volume': 8765432, 'marketCap': '$256.8B'},
        ],
        'dow': [
            {'symbol': 'UNH', 'name': 'UnitedHealth Group', 'price': 511.20, 'change': 3.80, 'changePercent': 0.75, 'volume': 3456789, 'marketCap': '$486.2B'},
            {'symbol': 'GS', 'name': 'Goldman Sachs', 'price': 445.70, 'change': -2.30, 'changePercent': -0.51, 'volume': 2345678, 'marketCap': '$156.3B'},
            {'symbol': 'HD', 'name': 'Home Depot', 'price': 385.90, 'change': 4.50, 'changePercent': 1.18, 'volume': 4567890, 'marketCap': '$398.7B'},
            {'symbol': 'V', 'name': 'Visa Inc.', 'price': 289.60, 'change': 1.20, 'changePercent': 0.42, 'volume': 6789012, 'marketCap': '$617.4B'},
        ],
        'russell': [
            {'symbol': 'GME', 'name': 'GameStop Corp.', 'price': 18.50, 'change': 0.75, 'changePercent': 4.23, 'volume': 12345678, 'marketCap': '$5.6B'},
            {'symbol': 'AMC', 'name': 'AMC Entertainment', 'price': 4.25, 'change': -0.15, 'changePercent': -3.41, 'volume': 23456789, 'marketCap': '$2.3B'},
            {'symbol': 'PLTR', 'name': 'Palantir Technologies', 'price': 26.80, 'change': 1.30, 'changePercent': 5.10, 'volume': 34567890, 'marketCap': '$58.2B'},
            {'symbol': 'BB', 'name': 'BlackBerry Limited', 'price': 2.75, 'change': -0.05, 'changePercent': -1.79, 'volume': 8765432, 'marketCap': '$1.6B'},
        ]
    }
    
    data = []
    stocks = us_stocks.get(market, [])
    
    for stock in stocks:
        data.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'price': float(stock['price']),
            'change': float(stock['change']),
            'changePercent': float(stock['changePercent']),
            'volume': int(stock['volume']),
            'marketCap': stock['marketCap'],
            'country': 'usa',
            'market': market.upper(),
            'date': end_date
        })
    
    return data

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
            'message': f'Successfully collected {len(data)} records from {market.upper()} market'
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