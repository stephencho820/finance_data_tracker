#!/usr/bin/env python3
"""
빠른 PostgreSQL 데이터 삽입 스크립트
"""

import psycopg2
import os
import sys
from datetime import datetime, timedelta
import logging
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        connection = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            database=os.getenv('PGDATABASE', 'postgres'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', ''),
            port=os.getenv('PGPORT', '5432')
        )
        return connection
    except Exception as e:
        logger.error(f"PostgreSQL 연결 오류: {e}")
        raise

def insert_sample_data():
    """샘플 데이터 빠른 삽입"""
    connection = get_database_connection()
    cursor = connection.cursor()
    
    # 주요 종목 데이터
    stocks = [
        ('005930', '삼성전자', 'KOSPI', 72000, 15000000, '430000000000000'),
        ('000660', 'SK하이닉스', 'KOSPI', 134000, 8000000, '97000000000000'),
        ('035420', 'NAVER', 'KOSPI', 180000, 1200000, '30000000000000'),
        ('051910', 'LG화학', 'KOSPI', 420000, 500000, '29000000000000'),
        ('006400', '삼성SDI', 'KOSPI', 350000, 800000, '26000000000000'),
        ('207940', '삼성바이오로직스', 'KOSPI', 850000, 200000, '62000000000000'),
        ('068270', '셀트리온', 'KOSPI', 180000, 1500000, '24000000000000'),
        ('035720', '카카오', 'KOSDAQ', 45000, 3000000, '16000000000000'),
        ('259960', '크래프톤', 'KOSDAQ', 220000, 800000, '11000000000000'),
        ('066570', 'LG전자', 'KOSDAQ', 95000, 2000000, '13000000000000'),
    ]
    
    # 최근 30일간 데이터 생성
    base_date = datetime.now() - timedelta(days=30)
    
    data_to_insert = []
    
    for days in range(30):
        current_date = base_date + timedelta(days=days)
        
        # 주말 제외
        if current_date.weekday() >= 5:
            continue
            
        date_str = current_date.strftime('%Y-%m-%d')
        
        # 시가총액 기준 랭킹
        cap_ranked = sorted(stocks, key=lambda x: int(x[5]), reverse=True)
        for rank, (code, name, market, price, volume, cap) in enumerate(cap_ranked, 1):
            # 일일 변동 적용
            daily_var = random.uniform(0.95, 1.05)
            open_price = price * random.uniform(0.98, 1.02)
            close_price = price * daily_var
            high_price = max(open_price, close_price) * random.uniform(1.00, 1.03)
            low_price = min(open_price, close_price) * random.uniform(0.97, 1.00)
            
            data_to_insert.append((
                date_str, code, name, market, 'market_cap', rank,
                round(open_price, 2), round(high_price, 2), 
                round(low_price, 2), round(close_price, 2),
                int(volume * random.uniform(0.8, 1.2)), cap
            ))
        
        # 거래량 기준 랭킹
        vol_ranked = sorted(stocks, key=lambda x: x[4], reverse=True)
        for rank, (code, name, market, price, volume, cap) in enumerate(vol_ranked, 1):
            # 일일 변동 적용
            daily_var = random.uniform(0.95, 1.05)
            open_price = price * random.uniform(0.98, 1.02)
            close_price = price * daily_var
            high_price = max(open_price, close_price) * random.uniform(1.00, 1.03)
            low_price = min(open_price, close_price) * random.uniform(0.97, 1.00)
            
            data_to_insert.append((
                date_str, code, name, market, 'volume', rank,
                round(open_price, 2), round(high_price, 2), 
                round(low_price, 2), round(close_price, 2),
                int(volume * random.uniform(0.8, 1.2)), cap
            ))
    
    # 데이터 삽입
    insert_query = """
    INSERT INTO daily_stock_data 
    (date, symbol, name, market, rank_type, rank, open_price, high_price, low_price, close_price, volume, market_cap)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (date, symbol, market, rank_type) DO UPDATE SET
        rank = EXCLUDED.rank,
        name = EXCLUDED.name,
        open_price = EXCLUDED.open_price,
        high_price = EXCLUDED.high_price,
        low_price = EXCLUDED.low_price,
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume,
        market_cap = EXCLUDED.market_cap
    """
    
    try:
        cursor.executemany(insert_query, data_to_insert)
        connection.commit()
        logger.info(f"✅ {len(data_to_insert)}개 데이터 삽입 완료")
        
        # 확인 쿼리
        cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
        total_count = cursor.fetchone()[0]
        logger.info(f"총 데이터 개수: {total_count:,}개")
        
    except Exception as e:
        logger.error(f"데이터 삽입 오류: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()

def main():
    """메인 실행 함수"""
    logger.info("PostgreSQL 빠른 데이터 삽입 시작")
    
    try:
        insert_sample_data()
        logger.info("데이터 삽입 완료")
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()