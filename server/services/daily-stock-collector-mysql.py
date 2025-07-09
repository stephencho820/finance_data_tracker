"""
MySQL 기반 일일 주식 데이터 수집 스크립트
매일 오전 8시에 전일 데이터를 수집하여 DB에 저장하고 5년치 데이터만 유지
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
from datetime import datetime, timedelta
import logging

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
    """MySQL 데이터베이스 연결"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'stock_db'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except Error as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
        raise

def get_market_data(date):
    """
    지정된 날짜의 시장 데이터를 pykrx API로 가져오는 함수
    KOSPI, KOSDAQ 시가총액 상위 500개 종목 데이터 수집
    """
    try:
        from pykrx import stock
        import pandas as pd
        
        date_str = date.strftime('%Y%m%d')
        all_data = []
        
        # KOSPI 데이터 수집
        logger.info(f"KOSPI 데이터 수집 시작: {date_str}")
        kospi_tickers = stock.get_market_ticker_list(date_str, market="KOSPI")
        
        if kospi_tickers:
            # 시가총액 기준으로 상위 250개 선택
            kospi_caps = {}
            for ticker in kospi_tickers[:500]:  # 효율성을 위해 상위 500개만 확인
                try:
                    cap = stock.get_market_cap_by_ticker(date_str, ticker)
                    if cap and len(cap) > 0:
                        kospi_caps[ticker] = cap.iloc[0]['시가총액']
                except:
                    continue
            
            # 시가총액 상위 250개 선택
            top_kospi = sorted(kospi_caps.items(), key=lambda x: x[1], reverse=True)[:250]
            
            # OHLCV 데이터 수집
            for ticker, market_cap in top_kospi:
                try:
                    ohlcv = stock.get_market_ohlcv_by_ticker(date_str, date_str, ticker)
                    if ohlcv is not None and len(ohlcv) > 0:
                        row = ohlcv.iloc[0]
                        company_name = stock.get_market_ticker_name(ticker)
                        
                        all_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'code': ticker,
                            'name': company_name,
                            'open': int(row['시가']) if pd.notna(row['시가']) else 0,
                            'high': int(row['고가']) if pd.notna(row['고가']) else 0,
                            'low': int(row['저가']) if pd.notna(row['저가']) else 0,
                            'close': int(row['종가']) if pd.notna(row['종가']) else 0,
                            'volume': int(row['거래량']) if pd.notna(row['거래량']) else 0,
                            'market_cap': market_cap
                        })
                except Exception as e:
                    logger.warning(f"KOSPI {ticker} 데이터 수집 실패: {e}")
                    continue
        
        # KOSDAQ 데이터 수집
        logger.info(f"KOSDAQ 데이터 수집 시작: {date_str}")
        kosdaq_tickers = stock.get_market_ticker_list(date_str, market="KOSDAQ")
        
        if kosdaq_tickers:
            # 시가총액 기준으로 상위 250개 선택
            kosdaq_caps = {}
            for ticker in kosdaq_tickers[:500]:  # 효율성을 위해 상위 500개만 확인
                try:
                    cap = stock.get_market_cap_by_ticker(date_str, ticker)
                    if cap and len(cap) > 0:
                        kosdaq_caps[ticker] = cap.iloc[0]['시가총액']
                except:
                    continue
            
            # 시가총액 상위 250개 선택
            top_kosdaq = sorted(kosdaq_caps.items(), key=lambda x: x[1], reverse=True)[:250]
            
            # OHLCV 데이터 수집
            for ticker, market_cap in top_kosdaq:
                try:
                    ohlcv = stock.get_market_ohlcv_by_ticker(date_str, date_str, ticker)
                    if ohlcv is not None and len(ohlcv) > 0:
                        row = ohlcv.iloc[0]
                        company_name = stock.get_market_ticker_name(ticker)
                        
                        all_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'code': ticker,
                            'name': company_name,
                            'open': int(row['시가']) if pd.notna(row['시가']) else 0,
                            'high': int(row['고가']) if pd.notna(row['고가']) else 0,
                            'low': int(row['저가']) if pd.notna(row['저가']) else 0,
                            'close': int(row['종가']) if pd.notna(row['종가']) else 0,
                            'volume': int(row['거래량']) if pd.notna(row['거래량']) else 0,
                            'market_cap': market_cap
                        })
                except Exception as e:
                    logger.warning(f"KOSDAQ {ticker} 데이터 수집 실패: {e}")
                    continue
        
        logger.info(f"{date.strftime('%Y-%m-%d')} 데이터 수집 완료: {len(all_data)}개")
        return all_data
        
    except Exception as e:
        logger.error(f"시장 데이터 수집 중 오류 발생: {e}")
        return []

def insert_daily_data(connection, data_list):
    """일일 데이터를 데이터베이스에 INSERT"""
    cursor = connection.cursor()
    
    insert_query = """
    INSERT INTO stock_daily (date, code, name, open, high, low, close, volume, market_cap)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        open = VALUES(open),
        high = VALUES(high),
        low = VALUES(low),
        close = VALUES(close),
        volume = VALUES(volume),
        market_cap = VALUES(market_cap)
    """
    
    try:
        # 데이터 변환 (딕셔너리 -> 튜플)
        insert_data = [
            (
                item['date'],
                item['code'],
                item['name'],
                item['open'],
                item['high'],
                item['low'],
                item['close'],
                item['volume'],
                item['market_cap']
            )
            for item in data_list
        ]
        
        cursor.executemany(insert_query, insert_data)
        connection.commit()
        
        logger.info(f"{len(insert_data)}개 데이터 INSERT 완료")
        return len(insert_data)
        
    except Error as e:
        logger.error(f"데이터 INSERT 오류: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def delete_old_data(connection, cutoff_date):
    """5년 이전 데이터 삭제"""
    cursor = connection.cursor()
    
    delete_query = "DELETE FROM stock_daily WHERE date < %s"
    
    try:
        cursor.execute(delete_query, (cutoff_date,))
        deleted_rows = cursor.rowcount
        connection.commit()
        
        logger.info(f"{cutoff_date} 이전 데이터 {deleted_rows}개 삭제 완료")
        return deleted_rows
        
    except Error as e:
        logger.error(f"오래된 데이터 삭제 오류: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def get_data_count(connection):
    """현재 저장된 데이터 개수 확인"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM stock_daily")
        count = cursor.fetchone()[0]
        return count
    except Error as e:
        logger.error(f"데이터 개수 조회 오류: {e}")
        return 0
    finally:
        cursor.close()

def main():
    """메인 실행 함수"""
    start_time = datetime.now()
    logger.info("=== 일일 주식 데이터 수집 시작 ===")
    
    try:
        # 전일 날짜 계산
        yesterday = datetime.now() - timedelta(days=1)
        
        # 5년 전 날짜 계산 (데이터 보관 기준)
        five_years_ago = datetime.now() - timedelta(days=5*365)
        
        logger.info(f"수집 대상 날짜: {yesterday.strftime('%Y-%m-%d')}")
        logger.info(f"삭제 기준 날짜: {five_years_ago.strftime('%Y-%m-%d')} 이전")
        
        # 데이터베이스 연결
        connection = get_database_connection()
        logger.info("데이터베이스 연결 성공")
        
        # 현재 데이터 개수 확인
        initial_count = get_data_count(connection)
        logger.info(f"수집 전 데이터 개수: {initial_count:,}개")
        
        # 전일 데이터 수집
        market_data = get_market_data(yesterday)
        
        if not market_data:
            logger.warning("수집된 데이터가 없습니다.")
            return
        
        # 데이터베이스에 INSERT
        inserted_count = insert_daily_data(connection, market_data)
        
        # 5년 이전 데이터 삭제
        deleted_count = delete_old_data(connection, five_years_ago.strftime('%Y-%m-%d'))
        
        # 최종 데이터 개수 확인
        final_count = get_data_count(connection)
        
        # 실행 시간 계산
        execution_time = datetime.now() - start_time
        
        # 결과 로깅
        logger.info("=== 수집 완료 결과 ===")
        logger.info(f"신규 데이터 추가: {inserted_count:,}개")
        logger.info(f"오래된 데이터 삭제: {deleted_count:,}개")
        logger.info(f"최종 데이터 개수: {final_count:,}개")
        logger.info(f"실행 시간: {execution_time.total_seconds():.2f}초")
        
        # 데이터 무결성 확인
        if final_count == initial_count + inserted_count - deleted_count:
            logger.info("✅ 데이터 무결성 확인 완료")
        else:
            logger.warning("⚠️ 데이터 개수 불일치 감지")
        
    except Exception as e:
        logger.error(f"스크립트 실행 중 오류 발생: {e}")
        sys.exit(1)
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logger.info("데이터베이스 연결 종료")
    
    logger.info("=== 일일 주식 데이터 수집 완료 ===")

if __name__ == "__main__":
    main()