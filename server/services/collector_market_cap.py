#!/usr/bin/env python3

import os, sys, logging, psycopg2, pandas as pd
from datetime import datetime, timedelta
from pykrx import stock
from psycopg2.extras import execute_batch

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


def get_db():
    return psycopg2.connect(host=os.getenv("PGHOST", "localhost"),
                            database=os.getenv("PGDATABASE", "postgres"),
                            user=os.getenv("PGUSER", "postgres"),
                            password=os.getenv("PGPASSWORD", ""),
                            port=os.getenv("PGPORT", "5432"),
                            sslmode="require")


def get_latest_trading_day(start_date: datetime) -> datetime:
    for i in range(10):  # 최대 10일 전까지 탐색
        date = start_date - timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        try:
            if stock.get_nearest_business_day_in_a_week(date_str) == date_str:
                return date
        except:
            continue
    raise ValueError("📛 최근 10일 내 거래일 없음")


def get_market_data(date: datetime):
    date_str = date.strftime("%Y%m%d")
    logger.info(f"📥 {date_str} 기준 시총 Top 200 수집 시작")

    # 시가총액 수집
    cap_kospi = stock.get_market_cap_by_ticker(
        date_str, market="KOSPI").sort_values("시가총액",
                                              ascending=False).head(200)
    cap_kosdaq = stock.get_market_cap_by_ticker(
        date_str, market="KOSDAQ").sort_values("시가총액",
                                               ascending=False).head(200)

    cap_kospi["market"] = "KOSPI"
    cap_kosdaq["market"] = "KOSDAQ"

    cap_df = pd.concat([cap_kospi, cap_kosdaq])
    cap_df = cap_df[["시가총액", "market"]].copy()

    tickers = cap_df.index.tolist()
    logger.info(f"🧾 종목 수: {len(tickers)}")

    # 종목명 매핑
    name_map = {
        ticker: stock.get_market_ticker_name(ticker)
        for ticker in tickers
    }

    # OHLCV 수집
    logger.info(f"📊 OHLCV 개별 종목 수집 시작...")
    ohlcv_data = {}
    for ticker in tickers:
        df = stock.get_market_ohlcv(date_str, date_str, ticker)
        if df.empty:
            continue
        row = df.iloc[0]
        ohlcv_data[ticker] = {
            "open": row["시가"],
            "high": row["고가"],
            "low": row["저가"],
            "close": row["종가"],
            "volume": row["거래량"],
        }

    # 교집합만 사용
    common_tickers = list(set(cap_df.index) & set(ohlcv_data.keys()))

    rows = []
    for ticker in common_tickers:
        row = cap_df.loc[ticker]
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "ticker": ticker,
            "name": name_map[ticker],
            "market": row["market"],  # ✅ market 추가
            "market_cap": int(row["시가총액"]),
            "open_price": int(ohlcv_data[ticker]["open"]),
            "high_price": int(ohlcv_data[ticker]["high"]),
            "low_price": int(ohlcv_data[ticker]["low"]),
            "close_price": int(ohlcv_data[ticker]["close"]),
            "volume": int(ohlcv_data[ticker]["volume"]),
            "best_k": None,
        })

    logger.info(f"✅ 최종 수집 종목 수: {len(rows)}")
    return rows


def insert_data(conn, rows):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM daily_market_cap;")  # 전체 초기화 후 삽입
        sql = """
            INSERT INTO daily_market_cap
            (date, ticker, name, market, market_cap,
             open_price, high_price, low_price,
             close_price, volume, best_k)
            VALUES (%(date)s, %(ticker)s, %(name)s, %(market)s, %(market_cap)s,
                    %(open_price)s, %(high_price)s, %(low_price)s,
                    %(close_price)s, %(volume)s, %(best_k)s)
        """
        execute_batch(cur, sql, rows, page_size=200)
        conn.commit()
    logger.info(f"📌 {len(rows)} rows inserted.")


def main():
    try:
        latest_date = get_latest_trading_day(datetime.now())
        rows = get_market_data(latest_date)

        if rows:
            conn = get_db()
            insert_data(conn, rows)
            conn.close()
        else:
            logger.warning("❗ 수집된 데이터 없음")

        logger.info("🎯 collector_market_cap 완료")
    except Exception as e:
        logger.error(f"🚨 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
