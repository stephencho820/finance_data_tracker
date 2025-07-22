"""
MySQL 기반 일일 주식 데이터 수집 스크립트
4개 랭킹 리스트 수집 후 중복 제거하여 종목 상세 데이터 수집
- KOSPI 시가총액 상위 500종목
- KOSDAQ 시가총액 상위 500종목  
- KOSPI 거래량 상위 500종목
- KOSDAQ 거래량 상위 500종목
"""

import mysql.connector
from mysql.connector import Error
import os
import sys
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import time

# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('/tmp/daily_stock_collector.log'),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)


def get_database_connection():
    """MySQL 데이터베이스 연결"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'stock_db'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            port=int(os.getenv('DB_PORT', 3306)))
        return connection
    except Error as e:
        logger.error(f"데이터베이스 연결 오류: {e}")
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
        logger.info(f"KOSPI 시가총액 랭킹 수집 시작: {date_str}")
        try:
            kospi_cap_df = stock.get_market_cap_by_date(
                date_str, date_str, "KOSPI")
            if kospi_cap_df is not None and len(kospi_cap_df) > 0:
                kospi_cap_sorted = kospi_cap_df.sort_values(
                    '시가총액', ascending=False).head(500)
                for rank, (ticker,
                           row) in enumerate(kospi_cap_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSPI',
                        'rank_type': 'market_cap',
                        'rank': rank,
                        'value': row['시가총액']
                    })
            logger.info(
                f"KOSPI 시가총액 랭킹 수집 완료: {len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='market_cap'])}개"
            )
        except Exception as e:
            logger.error(f"KOSPI 시가총액 랭킹 수집 실패: {e}")

        # 2. KOSDAQ 시가총액 상위 500종목
        logger.info(f"KOSDAQ 시가총액 랭킹 수집 시작: {date_str}")
        try:
            kosdaq_cap_df = stock.get_market_cap_by_date(
                date_str, date_str, "KOSDAQ")
            if kosdaq_cap_df is not None and len(kosdaq_cap_df) > 0:
                kosdaq_cap_sorted = kosdaq_cap_df.sort_values(
                    '시가총액', ascending=False).head(500)
                for rank, (ticker,
                           row) in enumerate(kosdaq_cap_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSDAQ',
                        'rank_type': 'market_cap',
                        'rank': rank,
                        'value': row['시가총액']
                    })
            logger.info(
                f"KOSDAQ 시가총액 랭킹 수집 완료: {len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='market_cap'])}개"
            )
        except Exception as e:
            logger.error(f"KOSDAQ 시가총액 랭킹 수집 실패: {e}")

        # 3. KOSPI 거래량 상위 500종목
        logger.info(f"KOSPI 거래량 랭킹 수집 시작: {date_str}")
        try:
            kospi_vol_df = stock.get_market_ohlcv_by_date(
                date_str, date_str, "KOSPI")
            if kospi_vol_df is not None and len(kospi_vol_df) > 0:
                kospi_vol_sorted = kospi_vol_df.sort_values(
                    '거래량', ascending=False).head(500)
                for rank, (ticker,
                           row) in enumerate(kospi_vol_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSPI',
                        'rank_type': 'volume',
                        'rank': rank,
                        'value': row['거래량']
                    })
            logger.info(
                f"KOSPI 거래량 랭킹 수집 완료: {len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='volume'])}개"
            )
        except Exception as e:
            logger.error(f"KOSPI 거래량 랭킹 수집 실패: {e}")

        # 4. KOSDAQ 거래량 상위 500종목
        logger.info(f"KOSDAQ 거래량 랭킹 수집 시작: {date_str}")
        try:
            kosdaq_vol_df = stock.get_market_ohlcv_by_date(
                date_str, date_str, "KOSDAQ")
            if kosdaq_vol_df is not None and len(kosdaq_vol_df) > 0:
                kosdaq_vol_sorted = kosdaq_vol_df.sort_values(
                    '거래량', ascending=False).head(500)
                for rank, (ticker,
                           row) in enumerate(kosdaq_vol_sorted.iterrows(), 1):
                    ranking_data.append({
                        'code': ticker,
                        'market': 'KOSDAQ',
                        'rank_type': 'volume',
                        'rank': rank,
                        'value': row['거래량']
                    })
            logger.info(
                f"KOSDAQ 거래량 랭킹 수집 완료: {len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='volume'])}개"
            )
        except Exception as e:
            logger.error(f"KOSDAQ 거래량 랭킹 수집 실패: {e}")

        logger.info(f"총 랭킹 데이터 수집 완료: {len(ranking_data)}개")
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

        logger.info(f"종목 상세 데이터 수집 시작: {len(unique_tickers)}개")

        for i, ticker in enumerate(unique_tickers):
            try:
                # OHLCV 데이터 수집
                ohlcv = stock.get_market_ohlcv_by_ticker(
                    date_str, date_str, ticker)
                if ohlcv is not None and len(ohlcv) > 0:
                    row = ohlcv.iloc[0]

                    # 종목명 가져오기
                    try:
                        company_name = stock.get_market_ticker_name(ticker)
                    except:
                        company_name = ticker

                    # 시가총액 가져오기
                    try:
                        cap_data = stock.get_market_cap_by_ticker(
                            date_str, ticker)
                        market_cap = cap_data.iloc[0][
                            '시가총액'] if cap_data is not None and len(
                                cap_data) > 0 else 0
                    except:
                        market_cap = 0

                    stock_details[ticker] = {
                        'name': company_name,
                        'open': int(row['시가']) if pd.notna(row['시가']) else 0,
                        'high': int(row['고가']) if pd.notna(row['고가']) else 0,
                        'low': int(row['저가']) if pd.notna(row['저가']) else 0,
                        'close': int(row['종가']) if pd.notna(row['종가']) else 0,
                        'volume':
                        int(row['거래량']) if pd.notna(row['거래량']) else 0,
                        'market_cap': market_cap
                    }

                    if (i + 1) % 100 == 0:
                        logger.info(
                            f"종목 상세 데이터 수집 진행: {i + 1}/{len(unique_tickers)}")
                        time.sleep(0.1)  # API 호출 제한 방지

            except Exception as e:
                logger.warning(f"종목 {ticker} 상세 데이터 수집 실패: {e}")
                continue

        logger.info(f"종목 상세 데이터 수집 완료: {len(stock_details)}개")
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
                'code': ticker,
                'market': rank_item['market'],
                'rank_type': rank_item['rank_type'],
                'rank': rank_item['rank'],
                'name': detail['name'],
                'open': detail['open'],
                'high': detail['high'],
                'low': detail['low'],
                'close': detail['close'],
                'volume': detail['volume'],
                'market_cap': detail['market_cap']
            })

    logger.info(f"데이터 결합 완료: {len(combined_data)}개")
    return combined_data


def insert_daily_data(connection, data_list):
    """일일 데이터를 데이터베이스에 INSERT"""
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO stock_daily (date, code, market, rank_type, rank, name, open, high, low, close, volume, market_cap)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        rank = VALUES(rank),
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
            (item['date'], item['code'], item['market'], item['rank_type'],
             item['rank'], item['name'], item['open'], item['high'],
             item['low'], item['close'], item['volume'], item['market_cap'])
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
        cursor.execute(delete_query, (cutoff_date, ))
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


def log_collection_result(connection,
                          collection_date,
                          status,
                          total_records,
                          execution_time,
                          error_message=None):
    """수집 결과를 collection_log 테이블에 기록"""
    cursor = connection.cursor()

    insert_query = """
    INSERT INTO collection_log (collection_date, status, total_records, execution_time, error_message)
    VALUES (%s, %s, %s, %s, %s)
    """

    try:
        cursor.execute(insert_query,
                       (collection_date.strftime('%Y-%m-%d'), status,
                        total_records, execution_time, error_message))
        connection.commit()
        logger.info(f"수집 결과 로그 기록 완료: {status}")
    except Error as e:
        logger.error(f"수집 결과 로그 기록 오류: {e}")
        connection.rollback()
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
        five_years_ago = datetime.now() - timedelta(days=5 * 365)

        logger.info(f"수집 대상 날짜: {yesterday.strftime('%Y-%m-%d')}")
        logger.info(f"삭제 기준 날짜: {five_years_ago.strftime('%Y-%m-%d')} 이전")

        # 데이터베이스 연결
        connection = get_database_connection()
        logger.info("데이터베이스 연결 성공")

        # 현재 데이터 개수 확인
        initial_count = get_data_count(connection)
        logger.info(f"수집 전 데이터 개수: {initial_count:,}개")

        # 1. 랭킹 리스트 수집
        ranking_data = get_ranking_lists(yesterday)

        if not ranking_data:
            logger.warning("수집된 랭킹 데이터가 없습니다.")
            return

        # 2. 중복 제거된 종목 리스트 생성
        unique_tickers = get_unique_tickers(ranking_data)
        logger.info(f"중복 제거 후 종목 수: {len(unique_tickers)}개")

        # 3. 종목별 상세 데이터 수집
        stock_details = get_stock_details(yesterday, unique_tickers)

        if not stock_details:
            logger.warning("수집된 종목 상세 데이터가 없습니다.")
            return

        # 4. 데이터 결합
        combined_data = combine_data(yesterday, ranking_data, stock_details)

        if not combined_data:
            logger.warning("결합된 데이터가 없습니다.")
            return

        # 5. 데이터베이스에 INSERT
        inserted_count = insert_daily_data(connection, combined_data)

        # 5년 이전 데이터 삭제
        deleted_count = delete_old_data(connection,
                                        five_years_ago.strftime('%Y-%m-%d'))

        # 최종 데이터 개수 확인
        final_count = get_data_count(connection)

        # 실행 시간 계산
        execution_time = datetime.now() - start_time

        # 결과 로깅
        logger.info("=== 수집 완료 결과 ===")
        logger.info(f"랭킹 데이터: {len(ranking_data):,}개")
        logger.info(f"중복 제거 후 종목: {len(unique_tickers):,}개")
        logger.info(f"신규 데이터 추가: {inserted_count:,}개")
        logger.info(f"오래된 데이터 삭제: {deleted_count:,}개")
        logger.info(f"최종 데이터 개수: {final_count:,}개")
        logger.info(f"실행 시간: {execution_time.total_seconds():.2f}초")

        # 데이터 무결성 확인
        if final_count == initial_count + inserted_count - deleted_count:
            logger.info("✅ 데이터 무결성 확인 완료")
        else:
            logger.warning("⚠️ 데이터 개수 불일치 감지")

        # 수집 결과 로그 기록
        log_collection_result(connection, yesterday, 'SUCCESS', inserted_count,
                              execution_time.total_seconds())

    except Exception as e:
        logger.error(f"스크립트 실행 중 오류 발생: {e}")

        # 오류 로그 기록
        try:
            if 'connection' in locals():
                log_collection_result(connection, yesterday, 'ERROR', 0,
                                      (datetime.now() -
                                       start_time).total_seconds(), str(e))
        except:
            pass

        sys.exit(1)

    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            logger.info("데이터베이스 연결 종료")

    logger.info("=== 일일 주식 데이터 수집 완료 ===")


if __name__ == "__main__":
    main()
