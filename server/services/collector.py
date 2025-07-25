#!/usr/bin/env python3

import os
import sys
import time
import logging
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timedelta
from pykrx import stock

# 로깅 설정
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[
                        logging.FileHandler("/tmp/daily_stock_collector.log"),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)


def get_db_connection():
    conn = psycopg2.connect(host=os.getenv("PGHOST", "localhost"),
                            database=os.getenv("PGDATABASE", "postgres"),
                            user=os.getenv("PGUSER", "postgres"),
                            password=os.getenv("PGPASSWORD", ""),
                            port=os.getenv("PGPORT", "5432"),
                            sslmode="require")
    return conn


def get_top200_tickers(conn):
    with conn.cursor() as cur:
        query = """
            SELECT ticker
            FROM daily_market_cap
            WHERE date = (SELECT MAX(date) FROM daily_market_cap)
            ORDER BY market_cap::numeric DESC
            LIMIT 200
        """
        cur.execute(query)
        rows = cur.fetchall()
        return [row[0] for row in rows]


def get_latest_working_day():
    today = datetime.today().date()
    for i in range(0, 10):
        date = today - timedelta(days=i)
        if stock.get_market_ohlcv_by_date(date.strftime("%Y%m%d"),
                                          date.strftime("%Y%m%d"),
                                          "005930").empty is False:
            return date
    raise Exception("최근 거래일을 찾을 수 없습니다.")


def fetch_ohlcv(ticker, start_date, end_date):
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        if df is None or df.empty:
            return []
        df = df.reset_index()
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "date": row["날짜"].strftime("%Y-%m-%d"),
                "ticker": ticker,
                "open_price": float(row["시가"]),
                "high_price": float(row["고가"]),
                "low_price": float(row["저가"]),
                "close_price": float(row["종가"]),
                "volume": int(row["거래량"]),
            })
        return rows
    except Exception as e:
        logger.warning(f"{ticker} OHLCV 수집 실패: {e}")
        return []


def insert_ohlcv(conn, rows):
    if not rows:
        return 0

    query = """
        INSERT INTO daily_stock_data
        (date, ticker, open_price, high_price, low_price, close_price, volume)
        VALUES
        (%(date)s, %(ticker)s, %(open_price)s, %(high_price)s, %(low_price)s, %(close_price)s, %(volume)s)
        ON CONFLICT (date, ticker) DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume;
    """
    with conn.cursor() as cur:
        execute_batch(cur, query, rows, page_size=500)
    conn.commit()
    return len(rows)


def update_market_cap_with_ohlcv(conn, rows):
    if not rows:
        return

    query = """
        UPDATE daily_market_cap
        SET open_price = %(open_price)s,
            high_price = %(high_price)s,
            low_price = %(low_price)s,
            close_price = %(close_price)s,
            volume = %(volume)s
        WHERE date = %(date)s AND ticker = %(ticker)s
    """
    with conn.cursor() as cur:
        execute_batch(cur, query, rows, page_size=100)
    conn.commit()


def main():
    start_time = time.time()
    logger.info("PostgreSQL 주식 데이터 수집 시작")

    # 최신 거래일 기준 설정
    end_date_obj = get_latest_working_day()
    start_date_obj = end_date_obj - timedelta(days=365)

    start_date = start_date_obj.strftime("%Y%m%d")
    end_date = end_date_obj.strftime("%Y%m%d")
    target_date_str = end_date_obj.strftime("%Y-%m-%d")

    logger.info(
        f"수집 기간: {start_date} ~ {end_date} (target: {target_date_str})")

    conn = get_db_connection()
    tickers = get_top200_tickers(conn)
    logger.info(f"Top200 ticker 수: {len(tickers)}")

    total_inserted = 0
    latest_ohlcv_rows = []

    for i, ticker in enumerate(tickers, 1):
        logger.info(f"[{i}/{len(tickers)}] {ticker} 수집 시작")
        rows = fetch_ohlcv(ticker, start_date, end_date)
        if not rows:
            continue

        inserted = insert_ohlcv(conn, rows)
        total_inserted += inserted
        logger.info(f"{ticker}: {inserted} rows 저장")

        latest_row = next((r for r in rows if r["date"] == target_date_str),
                          None)
        if latest_row:
            latest_ohlcv_rows.append(latest_row)

        time.sleep(1)

    logger.info("daily_market_cap 테이블에 OHLCV 병합 업데이트 중...")
    update_market_cap_with_ohlcv(conn, latest_ohlcv_rows)

    logger.info(f"전체 수집 완료. 총 {total_inserted:,} rows 저장.")
    logger.info(f"소요 시간: {time.time() - start_time:.2f} sec")
    conn.close()


if __name__ == "__main__":
    main()
