#!/usr/bin/env python3
"""
1년치 일일 데이터 수집 스크립트
매일 오전 8시에 실행되어 KOSPI/KOSDAQ 시가총액 top 200 종목의 데이터를 수집
"""

import sys
import json
import traceback
import psycopg2
from datetime import datetime, timedelta
import time
import os


def get_database_connection():
    """데이터베이스 연결 설정"""
    try:
        conn = psycopg2.connect(host=os.getenv('PGHOST'),
                                database=os.getenv('PGDATABASE'),
                                user=os.getenv('PGUSER'),
                                password=os.getenv('PGPASSWORD'),
                                port=os.getenv('PGPORT', 5432))
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}", file=sys.stderr)
        return None


def get_top_500_stocks(market):
    """시가총액 기준 상위 500개 종목 조회"""
    try:
        import pykrx.stock as stock
        from pykrx import stock as pykrx_stock

        # 최근 거래일 기준으로 조회
        today = datetime.now().strftime('%Y%m%d')

        # 시가총액 기준 상위 500개 종목 조회
        if market == 'KOSPI':
            tickers = pykrx_stock.get_market_ticker_list(today, market="KOSPI")
        elif market == 'KOSDAQ':
            tickers = pykrx_stock.get_market_ticker_list(today,
                                                         market="KOSDAQ")
        else:
            return []

        # 시가총액 데이터 가져오기
        market_cap_data = []
        for ticker in tickers[:500]:  # 최대 500개로 제한
            try:
                cap_df = pykrx_stock.get_market_cap_by_date(
                    today, today, ticker)
                if not cap_df.empty:
                    market_cap = cap_df.iloc[0]['시가총액']
                    name = pykrx_stock.get_market_ticker_name(ticker)
                    market_cap_data.append({
                        'symbol': ticker,
                        'name': name,
                        'market_cap': market_cap
                    })
            except:
                continue

        # 시가총액 기준 정렬
        market_cap_data.sort(key=lambda x: x['market_cap'], reverse=True)

        return market_cap_data[:500]

    except Exception as e:
        print(f"[ERROR] Failed to get top 500 stocks: {e}", file=sys.stderr)
        return []


def collect_historical_data(symbols, market, start_date, end_date):
    """5년치 일일 데이터 수집"""
    try:
        import pykrx.stock as stock
        from pykrx import stock as pykrx_stock

        start_date_fmt = start_date.strftime('%Y%m%d')
        end_date_fmt = end_date.strftime('%Y%m%d')

        collected_data = []

        print(f"[INFO] Collecting historical data for {len(symbols)} symbols",
              file=sys.stderr)

        for i, stock_info in enumerate(symbols):
            symbol = stock_info['symbol']
            name = stock_info['name']

            try:
                # OHLCV 데이터 가져오기
                ohlcv_df = pykrx_stock.get_market_ohlcv_by_date(
                    start_date_fmt, end_date_fmt, symbol)

                if not ohlcv_df.empty:
                    # 각 날짜별로 데이터 저장
                    for date_str, row in ohlcv_df.iterrows():
                        try:
                            # 시가총액 데이터 가져오기 (일별)
                            date_fmt = date_str.strftime('%Y%m%d')
                            market_cap = None
                            try:
                                cap_df = pykrx_stock.get_market_cap_by_date(
                                    date_fmt, date_fmt, symbol)
                                if not cap_df.empty:
                                    market_cap = str(cap_df.iloc[0]['시가총액'])
                            except:
                                pass

                            collected_data.append({
                                'symbol':
                                symbol,
                                'name':
                                name,
                                'date':
                                date_str.strftime('%Y-%m-%d'),
                                'open_price':
                                float(row['시가']) if row['시가'] else None,
                                'high_price':
                                float(row['고가']) if row['고가'] else None,
                                'low_price':
                                float(row['저가']) if row['저가'] else None,
                                'close_price':
                                float(row['종가']) if row['종가'] else None,
                                'volume':
                                int(row['거래량']) if row['거래량'] else None,
                                'market_cap':
                                market_cap,
                                'market':
                                market
                            })
                        except Exception as e:
                            continue

                # 진행률 출력
                if (i + 1) % 10 == 0:
                    print(f"[INFO] Processed {i + 1}/{len(symbols)} symbols",
                          file=sys.stderr)

            except Exception as e:
                print(f"[WARNING] Failed to collect data for {symbol}: {e}",
                      file=sys.stderr)
                continue

        return collected_data

    except Exception as e:
        print(f"[ERROR] Historical data collection failed: {e}",
              file=sys.stderr)
        return []


def save_to_database(data, conn):
    """데이터베이스에 저장"""
    try:
        cursor = conn.cursor()

        # 데이터 저장 쿼리
        insert_query = """
        INSERT INTO daily_stock_data 
        (symbol, name, date, open_price, high_price, low_price, close_price, volume, market_cap, market)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, date) DO UPDATE SET
        open_price = EXCLUDED.open_price,
        high_price = EXCLUDED.high_price,
        low_price = EXCLUDED.low_price,
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume,
        market_cap = EXCLUDED.market_cap,
        market = EXCLUDED.market
        """

        # 배치 단위로 저장
        batch_size = 1000
        total_saved = 0

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_values = []

            for item in batch:
                batch_values.append(
                    (item['symbol'], item['name'], item['date'],
                     item['open_price'], item['high_price'], item['low_price'],
                     item['close_price'], item['volume'], item['market_cap'],
                     item['market']))

            cursor.executemany(insert_query, batch_values)
            conn.commit()
            total_saved += len(batch)

            print(f"[INFO] Saved {total_saved}/{len(data)} records",
                  file=sys.stderr)

        cursor.close()
        return total_saved

    except Exception as e:
        print(f"[ERROR] Database save failed: {e}", file=sys.stderr)
        conn.rollback()
        return 0


def log_collection_result(market, total_stocks, status, error_message,
                          execution_time, conn):
    """수집 결과 로그 저장"""
    try:
        cursor = conn.cursor()

        log_query = """
        INSERT INTO data_collection_log 
        (collection_date, market, total_stocks, status, error_message, execution_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(log_query, (datetime.now().date(), market, total_stocks,
                                   status, error_message, execution_time))

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f"[ERROR] Failed to log collection result: {e}", file=sys.stderr)


def main():
    """메인 실행 함수"""
    start_time = time.time()

    try:
        # 입력 파라미터 파싱
        input_data = json.loads(
            sys.stdin.read()) if sys.stdin.isatty() == False else {
                "market": "KOSPI"
            }
        market = input_data.get('market', 'KOSPI')

        print(f"[INFO] Starting daily data collection for {market}",
              file=sys.stderr)

        # 데이터베이스 연결
        conn = get_database_connection()
        if not conn:
            raise Exception("Database connection failed")

        # 5년치 데이터 수집 기간 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)  # 5년

        print(
            f"[INFO] Collection period: {start_date.date()} to {end_date.date()}",
            file=sys.stderr)

        # 상위 500개 종목 조회
        top_500_stocks = get_top_500_stocks(market)
        if not top_500_stocks:
            raise Exception("Failed to get top 500 stocks")

        print(f"[INFO] Found {len(top_500_stocks)} top stocks",
              file=sys.stderr)

        # 5년치 데이터 수집
        historical_data = collect_historical_data(top_500_stocks, market,
                                                  start_date, end_date)
        if not historical_data:
            raise Exception("Failed to collect historical data")

        print(f"[INFO] Collected {len(historical_data)} historical records",
              file=sys.stderr)

        # 데이터베이스에 저장
        saved_count = save_to_database(historical_data, conn)

        # 실행 시간 계산
        execution_time = int((time.time() - start_time) * 1000)

        # 성공 로그 저장
        log_collection_result(market, saved_count, 'success', None,
                              execution_time, conn)

        conn.close()

        # 결과 반환
        print(
            json.dumps({
                'success': True,
                'message':
                f'Successfully collected and saved {saved_count} records for {market}',
                'data': {
                    'market': market,
                    'total_records': saved_count,
                    'execution_time': execution_time,
                    'period': f'{start_date.date()} to {end_date.date()}'
                }
            }))

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_message = str(e)

        # 데이터베이스 연결이 있으면 실패 로그 저장
        if 'conn' in locals() and conn:
            log_collection_result(market, 0, 'failed', error_message,
                                  execution_time, conn)
            conn.close()

        print(
            json.dumps({
                'success': False,
                'message': f'Data collection failed: {error_message}',
                'traceback': traceback.format_exc()
            }))


if __name__ == "__main__":
    main()
