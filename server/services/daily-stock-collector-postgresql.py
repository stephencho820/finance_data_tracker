#!/usr/bin/env python3
"""
PostgreSQL 기반 일일 주식 데이터 수집 스크립트
4개 랭킹 리스트 수집 후 중복 제거하여 종목 상세 데이터 수집
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
import time
from collections import defaultdict

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/daily_stock_collector.log'),
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
    """
    try:
        from pykrx import stock
        
        date_str = date.strftime('%Y%m%d')
        ranking_data = []
        
        # 1. KOSPI 시가총액 상위 500종목
        try:
            kospi_tickers = stock.get_market_ticker_list(date_str, market="KOSPI")
            kospi_cap_data = []
            for ticker in kospi_tickers:
                try:
                    cap = stock.get_market_cap_by_ticker(date_str, ticker)
                    if cap is not None and len(cap) > 0:
                        kospi_cap_data.append({
                            'ticker': ticker,
                            'cap': cap.iloc[0]['시가총액']
                        })
                except:
                    continue
            
            kospi_cap_sorted = sorted(kospi_cap_data, key=lambda x: x['cap'], reverse=True)[:500]
            for rank, item in enumerate(kospi_cap_sorted, 1):
                ranking_data.append({
                    'code': item['ticker'],
                    'market': 'KOSPI',
                    'rank_type': 'market_cap',
                    'rank': rank,
                    'value': item['cap']
                })
        except Exception as e:
            logger.warning(f"KOSPI 시가총액 랭킹 수집 실패: {e}")
        
        # 2. KOSDAQ 시가총액 상위 500종목
        try:
            kosdaq_tickers = stock.get_market_ticker_list(date_str, market="KOSDAQ")
            kosdaq_cap_data = []
            for ticker in kosdaq_tickers:
                try:
                    cap = stock.get_market_cap_by_ticker(date_str, ticker)
                    if cap is not None and len(cap) > 0:
                        kosdaq_cap_data.append({
                            'ticker': ticker,
                            'cap': cap.iloc[0]['시가총액']
                        })
                except:
                    continue
            
            kosdaq_cap_sorted = sorted(kosdaq_cap_data, key=lambda x: x['cap'], reverse=True)[:500]
            for rank, item in enumerate(kosdaq_cap_sorted, 1):
                ranking_data.append({
                    'code': item['ticker'],
                    'market': 'KOSDAQ',
                    'rank_type': 'market_cap',
                    'rank': rank,
                    'value': item['cap']
                })
        except Exception as e:
            logger.warning(f"KOSDAQ 시가총액 랭킹 수집 실패: {e}")
        
        # 3. KOSPI 거래량 상위 500종목
        try:
            kospi_vol_data = []
            for ticker in kospi_tickers:
                try:
                    ohlcv = stock.get_market_ohlcv_by_ticker(date_str, ticker)
                    if ohlcv is not None and len(ohlcv) > 0:
                        kospi_vol_data.append({
                            'ticker': ticker,
                            'volume': ohlcv.iloc[0]['거래량']
                        })
                except:
                    continue
            
            kospi_vol_sorted = sorted(kospi_vol_data, key=lambda x: x['volume'], reverse=True)[:500]
            for rank, item in enumerate(kospi_vol_sorted, 1):
                ranking_data.append({
                    'code': item['ticker'],
                    'market': 'KOSPI',
                    'rank_type': 'volume',
                    'rank': rank,
                    'value': item['volume']
                })
        except Exception as e:
            logger.warning(f"KOSPI 거래량 랭킹 수집 실패: {e}")
        
        # 4. KOSDAQ 거래량 상위 500종목
        try:
            kosdaq_vol_data = []
            for ticker in kosdaq_tickers:
                try:
                    ohlcv = stock.get_market_ohlcv_by_ticker(date_str, ticker)
                    if ohlcv is not None and len(ohlcv) > 0:
                        kosdaq_vol_data.append({
                            'ticker': ticker,
                            'volume': ohlcv.iloc[0]['거래량']
                        })
                except:
                    continue
            
            kosdaq_vol_sorted = sorted(kosdaq_vol_data, key=lambda x: x['volume'], reverse=True)[:500]
            for rank, item in enumerate(kosdaq_vol_sorted, 1):
                ranking_data.append({
                    'code': item['ticker'],
                    'market': 'KOSDAQ',
                    'rank_type': 'volume',
                    'rank': rank,
                    'value': item['volume']
                })
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
        
        date_str = date.strftime('%Y%m%d')
        stock_details = {}
        
        for ticker in unique_tickers:
            try:
                # OHLCV 데이터 수집
                ohlcv = stock.get_market_ohlcv_by_ticker(date_str, ticker)
                if ohlcv is not None and len(ohlcv) > 0:
                    data = ohlcv.iloc[0]
                    
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
                        'open': float(data['시가']) if data['시가'] else 0,
                        'high': float(data['고가']) if data['고가'] else 0,
                        'low': float(data['저가']) if data['저가'] else 0,
                        'close': float(data['종가']) if data['종가'] else 0,
                        'volume': int(data['거래량']) if data['거래량'] else 0,
                        'market_cap': str(market_cap)
                    }
                    
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

def delete_old_data(connection, cutoff_date):
    """5년 이전 데이터 삭제"""
    cursor = connection.cursor()
    
    delete_query = """
    DELETE FROM daily_stock_data 
    WHERE date < %s
    """
    
    try:
        cursor.execute(delete_query, (cutoff_date,))
        deleted_count = cursor.rowcount
        connection.commit()
        logger.info(f"5년 이전 데이터 삭제 완료: {deleted_count:,}개")
        return deleted_count
    except Exception as e:
        logger.error(f"데이터 삭제 오류: {e}")
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

def log_collection_result(connection, collection_date, status, total_records, execution_time, error_message=None):
    """수집 결과를 data_collection_log 테이블에 기록"""
    cursor = connection.cursor()
    
    insert_query = """
    INSERT INTO data_collection_log (collection_date, market, total_stocks, status, error_message, execution_time)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    try:
        cursor.execute(insert_query, (
            collection_date,
            'KOSPI+KOSDAQ',
            total_records,
            status,
            error_message,
            execution_time
        ))
        connection.commit()
        logger.info(f"수집 결과 로그 저장 완료: {status}")
    except Exception as e:
        logger.error(f"로그 저장 오류: {e}")
        connection.rollback()
    finally:
        cursor.close()

def main():
    """메인 실행 함수"""
    start_time = time.time()
    logger.info("PostgreSQL 일일 주식 데이터 수집 시작")
    
    # 어제 날짜 (주말 제외)
    collection_date = datetime.now() - timedelta(days=1)
    while collection_date.weekday() > 4:  # 주말 제외
        collection_date -= timedelta(days=1)
    
    logger.info(f"수집 날짜: {collection_date.strftime('%Y-%m-%d')}")
    
    connection = get_database_connection()
    
    try:
        # 1. 랭킹 리스트 수집
        ranking_data = get_ranking_lists(collection_date)
        
        if not ranking_data:
            error_msg = "랭킹 데이터 수집 실패"
            logger.error(error_msg)
            log_collection_result(connection, collection_date, 'failed', 0, 
                                int((time.time() - start_time) * 1000), error_msg)
            return
        
        logger.info(f"랭킹 데이터 수집 완료: {len(ranking_data)}개")
        
        # 2. 중복 제거된 종목 리스트 생성
        unique_tickers = get_unique_tickers(ranking_data)
        logger.info(f"중복 제거 후 종목 수: {len(unique_tickers)}개")
        
        # 3. 종목별 상세 데이터 수집
        stock_details = get_stock_details(collection_date, unique_tickers)
        
        if not stock_details:
            error_msg = "종목 상세 데이터 수집 실패"
            logger.error(error_msg)
            log_collection_result(connection, collection_date, 'failed', 0, 
                                int((time.time() - start_time) * 1000), error_msg)
            return
        
        logger.info(f"종목 상세 데이터 수집 완료: {len(stock_details)}개")
        
        # 4. 데이터 결합
        combined_data = combine_data(collection_date, ranking_data, stock_details)
        
        if not combined_data:
            error_msg = "데이터 결합 실패"
            logger.error(error_msg)
            log_collection_result(connection, collection_date, 'failed', 0, 
                                int((time.time() - start_time) * 1000), error_msg)
            return
        
        logger.info(f"데이터 결합 완료: {len(combined_data)}개")
        
        # 5. 데이터베이스에 INSERT
        inserted_count = insert_daily_data(connection, combined_data)
        
        # 6. 5년 이전 데이터 삭제
        cutoff_date = collection_date - timedelta(days=5*365)
        deleted_count = delete_old_data(connection, cutoff_date)
        
        # 7. 최종 데이터 개수 확인
        total_count = get_data_count(connection)
        
        # 8. 수집 결과 로그
        execution_time = int((time.time() - start_time) * 1000)
        log_collection_result(connection, collection_date, 'success', inserted_count, execution_time)
        
        logger.info("=== 일일 데이터 수집 완료 ===")
        logger.info(f"수집 날짜: {collection_date.strftime('%Y-%m-%d')}")
        logger.info(f"수집 데이터: {inserted_count:,}개")
        logger.info(f"삭제 데이터: {deleted_count:,}개")
        logger.info(f"총 DB 데이터: {total_count:,}개")
        logger.info(f"실행 시간: {execution_time:,}ms")
        
    except Exception as e:
        error_msg = f"수집 중 오류 발생: {e}"
        logger.error(error_msg)
        log_collection_result(connection, collection_date, 'failed', 0, 
                            int((time.time() - start_time) * 1000), error_msg)
    finally:
        connection.close()

if __name__ == "__main__":
    main()