#!/usr/bin/env python3
import json
import sys
import random
import traceback
from datetime import datetime, timedelta

def collect_korean_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect sample Korean stock data"""
    data = []
    
    # Sample Korean stock data
    sample_stocks = [
        {"symbol": "005930", "name": "삼성전자", "current_price": 75000, "market_cap": 460000000000000, "pe_ratio": 22.5, "pbr": 1.8, "dividend_yield": 2.1, "volume": 12000000},
        {"symbol": "000660", "name": "SK하이닉스", "current_price": 130000, "market_cap": 95000000000000, "pe_ratio": 18.3, "pbr": 1.5, "dividend_yield": 1.8, "volume": 8000000},
        {"symbol": "035420", "name": "NAVER", "current_price": 190000, "market_cap": 31000000000000, "pe_ratio": 28.1, "pbr": 2.2, "dividend_yield": 0.5, "volume": 3000000},
        {"symbol": "051910", "name": "LG화학", "current_price": 520000, "market_cap": 36000000000000, "pe_ratio": 15.7, "pbr": 1.1, "dividend_yield": 1.2, "volume": 2000000},
        {"symbol": "006400", "name": "삼성SDI", "current_price": 420000, "market_cap": 28000000000000, "pe_ratio": 19.2, "pbr": 1.9, "dividend_yield": 0.8, "volume": 1500000},
        {"symbol": "207940", "name": "삼성바이오로직스", "current_price": 850000, "market_cap": 69000000000000, "pe_ratio": 45.2, "pbr": 8.1, "dividend_yield": 0.0, "volume": 500000},
        {"symbol": "005490", "name": "POSCO홀딩스", "current_price": 380000, "market_cap": 31000000000000, "pe_ratio": 12.3, "pbr": 0.9, "dividend_yield": 3.2, "volume": 1200000},
        {"symbol": "035720", "name": "카카오", "current_price": 65000, "market_cap": 26000000000000, "pe_ratio": 35.8, "pbr": 2.7, "dividend_yield": 0.0, "volume": 2800000},
        {"symbol": "068270", "name": "셀트리온", "current_price": 180000, "market_cap": 23000000000000, "pe_ratio": 25.4, "pbr": 3.2, "dividend_yield": 0.0, "volume": 1800000},
        {"symbol": "373220", "name": "LG에너지솔루션", "current_price": 450000, "market_cap": 107000000000000, "pe_ratio": 21.7, "pbr": 2.1, "dividend_yield": 0.0, "volume": 3200000},
    ]
    
    # Apply limit
    max_count = min(limit or 10, len(sample_stocks))
    selected_stocks = sample_stocks[:max_count]
    
    for stock in selected_stocks:
        # Add some random variation
        price_change = random.uniform(-0.05, 0.05)
        current_price = stock["current_price"] * (1 + price_change)
        change = stock["current_price"] * price_change
        change_percent = price_change * 100
        
        data.append({
            'symbol': stock["symbol"],
            'name': stock["name"],
            'current_price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': stock["volume"],
            'market_cap': stock["market_cap"],
            'pe_ratio': stock["pe_ratio"],
            'pbr': stock["pbr"],
            'eps': round(current_price / stock["pe_ratio"], 2) if stock["pe_ratio"] > 0 else 0,
            'dividend_yield': stock["dividend_yield"],
            'week_52_high': round(current_price * 1.2, 2),
            'week_52_low': round(current_price * 0.8, 2),
            'beta': round(random.uniform(0.8, 1.5), 2),
            'shares_outstanding': stock["market_cap"] // current_price,
            'book_value': round(current_price / stock["pbr"], 2) if stock["pbr"] > 0 else 0,
            'revenue': random.randint(5000000000000, 50000000000000),
            'net_income': random.randint(1000000000000, 10000000000000),
            'debt_to_equity': round(random.uniform(0.2, 1.5), 2),
            'roe': round(random.uniform(5, 25), 2),
            'roa': round(random.uniform(3, 15), 2),
            'operating_margin': round(random.uniform(5, 20), 2),
            'profit_margin': round(random.uniform(3, 15), 2),
            'revenue_growth': round(random.uniform(-10, 30), 2),
            'earnings_growth': round(random.uniform(-15, 40), 2),
            'current_ratio': round(random.uniform(1.2, 3.5), 2),
            'quick_ratio': round(random.uniform(0.8, 2.5), 2),
            'price_to_sales': round(random.uniform(1, 5), 2),
            'price_to_cash_flow': round(random.uniform(8, 25), 2),
            'enterprise_value': stock["market_cap"] * random.uniform(1.1, 1.3),
            'ev_to_revenue': round(random.uniform(2, 8), 2),
            'ev_to_ebitda': round(random.uniform(10, 30), 2),
            'free_cash_flow': random.randint(500000000000, 5000000000000),
            'sector': random.choice(['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer']),
            'industry': random.choice(['Semiconductors', 'Software', 'Pharmaceuticals', 'Banking', 'Retail']),
            'country': 'Korea',
            'market': market.upper(),
            'date': end_date
        })
    
    # Sort data by specified criteria
    if sort_by and data:
        reverse_sort = True
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

def collect_us_data(start_date, end_date, market, sort_by=None, limit=None):
    """Collect sample US stock data"""
    data = []
    
    # Sample US stock data
    sample_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "current_price": 195.0, "market_cap": 3000000000000, "pe_ratio": 29.2, "pbr": 46.8, "dividend_yield": 0.5, "volume": 45000000},
        {"symbol": "MSFT", "name": "Microsoft Corp.", "current_price": 415.0, "market_cap": 3100000000000, "pe_ratio": 35.1, "pbr": 13.2, "dividend_yield": 0.7, "volume": 25000000},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "current_price": 142.0, "market_cap": 1800000000000, "pe_ratio": 26.8, "pbr": 5.9, "dividend_yield": 0.0, "volume": 28000000},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "current_price": 155.0, "market_cap": 1600000000000, "pe_ratio": 52.1, "pbr": 8.4, "dividend_yield": 0.0, "volume": 35000000},
        {"symbol": "TSLA", "name": "Tesla Inc.", "current_price": 245.0, "market_cap": 780000000000, "pe_ratio": 62.5, "pbr": 9.1, "dividend_yield": 0.0, "volume": 85000000},
        {"symbol": "META", "name": "Meta Platforms Inc.", "current_price": 485.0, "market_cap": 1200000000000, "pe_ratio": 25.2, "pbr": 7.8, "dividend_yield": 0.4, "volume": 18000000},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "current_price": 135.0, "market_cap": 3300000000000, "pe_ratio": 65.8, "pbr": 28.5, "dividend_yield": 0.03, "volume": 220000000},
        {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc.", "current_price": 445.0, "market_cap": 950000000000, "pe_ratio": 10.8, "pbr": 1.6, "dividend_yield": 0.0, "volume": 3500000},
        {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "current_price": 575.0, "market_cap": 540000000000, "pe_ratio": 28.5, "pbr": 6.2, "dividend_yield": 1.3, "volume": 2800000},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "current_price": 155.0, "market_cap": 410000000000, "pe_ratio": 15.2, "pbr": 5.8, "dividend_yield": 2.9, "volume": 8500000},
    ]
    
    # Apply limit
    max_count = min(limit or 10, len(sample_stocks))
    selected_stocks = sample_stocks[:max_count]
    
    for stock in selected_stocks:
        # Add some random variation
        price_change = random.uniform(-0.03, 0.03)
        current_price = stock["current_price"] * (1 + price_change)
        change = stock["current_price"] * price_change
        change_percent = price_change * 100
        
        data.append({
            'symbol': stock["symbol"],
            'name': stock["name"],
            'current_price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': stock["volume"],
            'market_cap': stock["market_cap"],
            'pe_ratio': stock["pe_ratio"],
            'pbr': stock["pbr"],
            'eps': round(current_price / stock["pe_ratio"], 2) if stock["pe_ratio"] > 0 else 0,
            'dividend_yield': stock["dividend_yield"],
            'week_52_high': round(current_price * 1.15, 2),
            'week_52_low': round(current_price * 0.85, 2),
            'beta': round(random.uniform(0.7, 1.8), 2),
            'shares_outstanding': stock["market_cap"] // current_price,
            'book_value': round(current_price / stock["pbr"], 2) if stock["pbr"] > 0 else 0,
            'revenue': random.randint(50000000000, 500000000000),
            'net_income': random.randint(10000000000, 100000000000),
            'debt_to_equity': round(random.uniform(0.1, 1.2), 2),
            'roe': round(random.uniform(8, 30), 2),
            'roa': round(random.uniform(5, 20), 2),
            'operating_margin': round(random.uniform(10, 30), 2),
            'profit_margin': round(random.uniform(8, 25), 2),
            'revenue_growth': round(random.uniform(-5, 25), 2),
            'earnings_growth': round(random.uniform(-10, 35), 2),
            'current_ratio': round(random.uniform(1.5, 4.0), 2),
            'quick_ratio': round(random.uniform(1.0, 3.0), 2),
            'price_to_sales': round(random.uniform(2, 12), 2),
            'price_to_cash_flow': round(random.uniform(15, 40), 2),
            'enterprise_value': stock["market_cap"] * random.uniform(1.05, 1.25),
            'ev_to_revenue': round(random.uniform(3, 15), 2),
            'ev_to_ebitda': round(random.uniform(15, 45), 2),
            'free_cash_flow': random.randint(5000000000, 80000000000),
            'sector': random.choice(['Technology', 'Healthcare', 'Finance', 'Consumer Discretionary', 'Communication']),
            'industry': random.choice(['Software', 'Semiconductors', 'Pharmaceuticals', 'E-commerce', 'Social Media']),
            'country': 'USA',
            'market': market.upper(),
            'date': end_date
        })
    
    # Sort data by specified criteria
    if sort_by and data:
        reverse_sort = True
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

if __name__ == "__main__":
    main()