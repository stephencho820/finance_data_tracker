#!/usr/bin/env python3

import os
import psycopg2
from pykrx import stock
from datetime import datetime, timedelta
import logging
import sys

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('/tmp/colletor_market_cap.log'),
                        logging.StreamHandler(sys.stdout)
                    ])
logger = logging.getLogger(__name__)


def get_database_connection():
    conn = psycopg2.connect(host=os.getenv('PGHOST', 'localhost'),
                            database=os.getenv('PGDATABASE', 'postgres'),
                            user=os.getenv('PGUSER', 'postgres'),
                            password=os.getenv('PGPASSWORD', ''),
                            port=os.getenv('PGPORT', '5432'),
                            sslmode="require")
    return conn


def is_trading_day(date_str):
    try:
        nearest = stock.get_nearest_business_day_in_a_week(date_str)
        return nearest == date_str
    except Exception as e:
        logger.warning(f"휴장일 체크 오류: {e}")
        return False


def get_all_market_cap(date_str):
    try:
        cap_kospi = stock.get_market_cap_by_ticker(date_str, market="KOSPI")
        cap_kosdaq = stock.get_market_cap_by_ticker(date_str, market="KOSDAQ")

        combined_df = cap_kospi.append(cap_kosdaq)
        combined_df = combined_df.reset_index()
        combined_df = combined_df.rename(columns={
            "티커": "ticker",
            "시가총액": "market_cap"
        })

        rows = []
        for _, row in combined_df.iterrows():
            rows.append({
                "date":
                datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d"),
                "ticker":
                row["ticker"],
                "market_cap":
                int(row["market_cap"])
            })

        return rows
    except Exception as e:
        logger.error(f"시가총액 수집 실패: {e}")
        return []


def insert_market_cap(conn, rows):
    insert_sql = """
        INSERT INTO daily_market_cap
        (date, ticker, market_cap)
        VALUES (%(date)s, %(ticker)s, %(market_cap)s)
        ON CONFLICT (date, ticker)
        DO UPDATE SET market_cap = EXCLUDED.market_cap;
    """
    try:
        with conn.cursor() as cur:
            cur.executemany(insert_sql, rows)
        conn.commit()
        logger.info(f"{len(rows)} rows inserted into daily_market_cap")
    except Exception as e:
        conn.rollback()
        logger.error(f"시가총액 insert 오류: {e}")


def main():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.strftime("%Y%m%d")

    if not is_trading_day(date_str):
        logger.info(f"{date_str} 휴장일, skip.")
        return

    rows = get_all_market_cap(date_str)

    if rows:
        conn = get_database_connection()
        try:
            insert_market_cap(conn, rows)
        finally:
            conn.close()


if __name__ == "__main__":
    main()
