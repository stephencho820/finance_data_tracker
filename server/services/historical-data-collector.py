#!/usr/bin/env python3
"""
PostgreSQL 5년치 역사적 데이터 수집 스크립트
2025년 7월 8일부터 5년전까지 4개 랭킹 리스트 데이터 수집
- KOSPI 시가총액 상위 500종목
- KOSDAQ 시가총액 상위 500종목
- KOSPI 거래량 상위 500종목
- KOSDAQ 거래량 상위 500종목
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import sys
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import time
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/historical_data_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
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

def get_ranking_lists(date):
    """
    4개 랭킹 리스트 수집
    - KOSPI 시가총액 상위 500종목
    - KOSDAQ 시가총액 상위 500종목
    - KOSPI 거래량 상위 500종목
    - KOSDAQ 거래량 상위 500종목
    """
    try:
        from pykrx import stock
        import pandas as pd
        
        date_str = date.strftime('%Y%m%d')
        ranking_data = []
        
        # 1. KOSPI 시가총액 상위 500종목
        logger.info(f"KOSPI 시가총액 랭킹 수집: {date_str}")
        try:
            kospi_cap_df = stock.get_market_cap_by_date(date_str, date_str, "KOSPI")
            if kospi_cap_df is not None and len(kospi_cap_df) > 0:
                kospi_cap_sorted = kospi_cap_df.sort_values('시가총액', ascending=False).head(500)
                for rank, (ticker, row) in enumerate(kospi_cap_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSPI',
                        'rank_type': 'market_cap',
                        'rank': rank,
                        'value': row['시가총액']
                    })
                logger.info(f"KOSPI 시가총액: {len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='market_cap'])}개")
        except Exception as e:
            logger.warning(f"KOSPI 시가총액 랭킹 수집 실패: {e}")
        
        # 2. KOSDAQ 시가총액 상위 500종목
        logger.info(f"KOSDAQ 시가총액 랭킹 수집: {date_str}")
        try:
            kosdaq_cap_df = stock.get_market_cap_by_date(date_str, date_str, "KOSDAQ")
            if kosdaq_cap_df is not None and len(kosdaq_cap_df) > 0:
                kosdaq_cap_sorted = kosdaq_cap_df.sort_values('시가총액', ascending=False).head(500)
                for rank, (ticker, row) in enumerate(kosdaq_cap_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSDAQ',
                        'rank_type': 'market_cap',
                        'rank': rank,
                        'value': row['시가총액']
                    })
                logger.info(f"KOSDAQ 시가총액: {len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='market_cap'])}개")
        except Exception as e:
            logger.warning(f"KOSDAQ 시가총액 랭킹 수집 실패: {e}")
        
        # 3. KOSPI 거래량 상위 500종목
        logger.info(f"KOSPI 거래량 랭킹 수집: {date_str}")
        try:
            kospi_vol_df = stock.get_market_ohlcv_by_date(date_str, date_str, "KOSPI")
            if kospi_vol_df is not None and len(kospi_vol_df) > 0:
                kospi_vol_sorted = kospi_vol_df.sort_values('거래량', ascending=False).head(500)
                for rank, (ticker, row) in enumerate(kospi_vol_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSPI',
                        'rank_type': 'volume',
                        'rank': rank,
                        'value': row['거래량']
                    })
                logger.info(f"KOSPI 거래량: {len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='volume'])}개")
        except Exception as e:
            logger.warning(f"KOSPI 거래량 랭킹 수집 실패: {e}")
        
        # 4. KOSDAQ 거래량 상위 500종목
        logger.info(f"KOSDAQ 거래량 랭킹 수집: {date_str}")
        try:
            kosdaq_vol_df = stock.get_market_ohlcv_by_date(date_str, date_str, "KOSDAQ")
            if kosdaq_vol_df is not None and len(kosdaq_vol_df) > 0:
                kosdaq_vol_sorted = kosdaq_vol_df.sort_values('거래량', ascending=False).head(500)
                for rank, (ticker, row) in enumerate(kosdaq_vol_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSDAQ',
                        'rank_type': 'volume',
                        'rank': rank,
                        'value': row['거래량']
                    })
                logger.info(f"KOSDAQ 거래량: {len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='volume'])}개")
        except Exception as e:
            logger.warning(f"KOSDAQ 거래량 랭킹 수집 실패: {e}")
        
        return ranking_data
        
    except Exception as e:
        logger.error(f"랭킹 리스트 수집 중 오류 발생: {e}")
        return []

def get_unique_tickers(ranking_data):
    """랭킹 데이터에서 중복 제거된 종목 코드 리스트 반환"""
    unique_tickers = set()
    for item in ranking_data:
        unique_tickers.add(item['code'])
    return list(unique_tickers)

def get_stock_details(date, unique_tickers):
    """종목별 상세 데이터 수집"""
    try:
        from pykrx import stock
        import pandas as pd
        
        date_str = date.strftime('%Y%m%d')
        stock_details = {}
        
        for i, ticker in enumerate(unique_tickers):
            try:
                # OHLCV 데이터 수집
                ohlcv = stock.get_market_ohlcv_by_ticker(date_str, date_str, ticker)
                if ohlcv is not None and len(ohlcv) > 0:
                    row = ohlcv.iloc[0]
                    
                    # 종목명 가져오기
                    try:
                        company_name = stock.get_market_ticker_name(ticker)
                    except:
                        company_name = ticker
                    
                    # 시가총액 가져오기
                    try:
                        cap_data = stock.get_market_cap_by_ticker(date_str, ticker)
                        market_cap = cap_data.iloc[0]['시가총액'] if cap_data is not None and len(cap_data) > 0 else 0
                    except:
                        market_cap = 0
                    
                    stock_details[ticker] = {
                        'name': company_name,
                        'open': float(row['시가']) if pd.notna(row['시가']) else 0,
                        'high': float(row['고가']) if pd.notna(row['고가']) else 0,
                        'low': float(row['저가']) if pd.notna(row['저가']) else 0,
                        'close': float(row['종가']) if pd.notna(row['종가']) else 0,
                        'volume': int(row['거래량']) if pd.notna(row['거래량']) else 0,
                        'market_cap': str(market_cap)
                    }
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"종목 상세 데이터 수집 진행: {i + 1}/{len(unique_tickers)}")
                        time.sleep(0.1)  # API 호출 제한 방지
                
            except Exception as e:
                logger.warning(f"종목 {ticker} 상세 데이터 수집 실패: {e}")
                continue
        
        return stock_details
        
    except Exception as e:
        logger.error(f"종목 상세 데이터 수집 중 오류 발생: {e}")
        return {}

def combine_data(date, ranking_data, stock_details):
    """랭킹 데이터와 종목 상세 데이터를 결합"""
    combined_data = []
    
    for rank_item in ranking_data:
        ticker = rank_item['code']
        
        if ticker in stock_details:
            detail = stock_details[ticker]
            
            combined_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'symbol': ticker,
                'market': rank_item['market'],
                'rank_type': rank_item['rank_type'],
                'rank': rank_item['rank'],
                'name': detail['name'],
                'open_price': detail['open'],
                'high_price': detail['high'],
                'low_price': detail['low'],
                'close_price': detail['close'],
                'volume': detail['volume'],
                'market_cap': detail['market_cap']
            })
    
    return combined_data

def insert_daily_data(connection, data_list):
    """PostgreSQL에 일일 데이터 INSERT"""
    cursor = connection.cursor()
    
    insert_query = """
    INSERT INTO daily_stock_data (date, symbol, market, rank_type, rank, name, open_price, high_price, low_price, close_price, volume, market_cap)
    VALUES (%(date)s, %(symbol)s, %(market)s, %(rank_type)s, %(rank)s, %(name)s, %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, %(volume)s, %(market_cap)s)
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
        cursor.executemany(insert_query, data_list)
        connection.commit()
        logger.info(f"{len(data_list)}개 데이터 INSERT 완료")
        return len(data_list)
    except Exception as e:
        logger.error(f"데이터 INSERT 오류: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def get_data_count(connection):
    """현재 저장된 데이터 개수 확인"""
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM daily_stock_data")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"데이터 개수 조회 오류: {e}")
        return 0
    finally:
        cursor.close()

def collect_historical_data(start_date, end_date):
    """5년치 역사적 데이터 수집"""
    logger.info(f"5년치 역사적 데이터 수집 시작: {start_date} ~ {end_date}")
    
    connection = get_database_connection()
    
    # 현재 데이터 개수 확인
    initial_count = get_data_count(connection)
    logger.info(f"수집 전 데이터 개수: {initial_count:,}개")
    
    current_date = start_date
    total_inserted = 0
    processed_dates = 0
    
    while current_date >= end_date:
        try:
            logger.info(f"수집 중: {current_date.strftime('%Y-%m-%d')} ({processed_dates + 1}일차)")
            
            # 1. 랭킹 리스트 수집
            ranking_data = get_ranking_lists(current_date)
            
            if not ranking_data:
                logger.warning(f"{current_date.strftime('%Y-%m-%d')} 랭킹 데이터 없음")
                current_date -= timedelta(days=1)
                continue
            
            # 2. 중복 제거된 종목 리스트 생성
            unique_tickers = get_unique_tickers(ranking_data)
            logger.info(f"중복 제거 후 종목 수: {len(unique_tickers)}개")
            
            # 3. 종목별 상세 데이터 수집
            stock_details = get_stock_details(current_date, unique_tickers)
            
            if not stock_details:
                logger.warning(f"{current_date.strftime('%Y-%m-%d')} 종목 상세 데이터 없음")
                current_date -= timedelta(days=1)
                continue
            
            # 4. 데이터 결합
            combined_data = combine_data(current_date, ranking_data, stock_details)
            
            if not combined_data:
                logger.warning(f"{current_date.strftime('%Y-%m-%d')} 결합된 데이터 없음")
                current_date -= timedelta(days=1)
                continue
            
            # 5. 데이터베이스에 INSERT
            inserted_count = insert_daily_data(connection, combined_data)
            total_inserted += inserted_count
            
            processed_dates += 1
            
            # 진행 상황 보고
            if processed_dates % 10 == 0:
                current_count = get_data_count(connection)
                logger.info(f"진행 상황: {processed_dates}일 처리 완료, 총 {total_inserted:,}개 데이터 수집, 현재 DB 데이터: {current_count:,}개")
            
            # API 호출 제한 방지
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"{current_date.strftime('%Y-%m-%d')} 수집 중 오류: {e}")
        
        current_date -= timedelta(days=1)
    
    # 최종 결과
    final_count = get_data_count(connection)
    logger.info("=== 5년치 데이터 수집 완료 ===")
    logger.info(f"처리된 날짜: {processed_dates}일")
    logger.info(f"총 수집 데이터: {total_inserted:,}개")
    logger.info(f"최종 DB 데이터: {final_count:,}개")
    
    connection.close()

def main():
    """메인 실행 함수"""
    logger.info("PostgreSQL 5년치 역사적 데이터 수집 시작")
    
    # 2024년 12월 31일부터 5년 전까지 (실제 존재하는 데이터 범위)
    start_date = datetime(2024, 12, 31)
    end_date = datetime(2020, 1, 1)
    
    logger.info(f"수집 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    try:
        collect_historical_data(start_date, end_date)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"수집 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()