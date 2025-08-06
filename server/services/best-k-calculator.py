#!/usr/bin/env python3

import os
import sys
import json
import logging
import traceback
import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pykrx import stock

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stderr)])
logger = logging.getLogger(__name__)

# 기간별 설정 매핑
PERIOD_CONFIG = {
    "days_3": {
        "days": 3,
        "type": "days_3"
    },
    "week_1": {
        "days": 7,
        "type": "week_1"
    },
    "month_1": {
        "days": 30,
        "type": "month_1"
    },
    "month_3": {
        "days": 90,
        "type": "month_3"
    },
    "quarter": {
        "days": 90,
        "type": "month_3"
    },  # quarter = 3months
    "half_year": {
        "days": 180,
        "type": "half_year"
    },
    "year_1": {
        "days": 365,
        "type": "year_1"
    }
}


def get_database_connection():
    try:
        conn = psycopg2.connect(host=os.getenv('PGHOST', 'localhost'),
                                database=os.getenv('PGDATABASE', 'postgres'),
                                user=os.getenv('PGUSER', 'postgres'),
                                password=os.getenv('PGPASSWORD', ''),
                                port=os.getenv('PGPORT', 5432),
                                sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def calculate_period_dates(period_type, start_date=None, end_date=None):
    today = datetime.now().date()

    if period_type == "custom":
        if not start_date or not end_date:
            raise ValueError("커스텀 기간 선택 시 시작일과 종료일이 필요합니다")
        return start_date, end_date

    end_date_str = today.strftime("%Y-%m-%d")

    if period_type in PERIOD_CONFIG:
        days = PERIOD_CONFIG[period_type]["days"]
        start_date_obj = today - timedelta(days=days)
        start_date_str = start_date_obj.strftime("%Y-%m-%d")
        return start_date_str, end_date_str

    # 기본값
    start_date_obj = today - timedelta(days=30)
    start_date_str = start_date_obj.strftime("%Y-%m-%d")
    return start_date_str, end_date_str


def get_top_200_tickers(conn):
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT ticker, name, market, market_cap, close_price
                FROM daily_market_cap
                WHERE date = (SELECT MAX(date) FROM daily_market_cap)
                ORDER BY market_cap::numeric DESC
                LIMIT 200
            """
            cursor.execute(query)
            results = cursor.fetchall()

            return [{
                "ticker": row[0],
                "name": row[1],
                "market": row[2],
                "market_cap": row[3],
                "close_price": row[4]
            } for row in results]

    except Exception as e:
        logger.error(f"Failed to get top 200 tickers: {e}")
        return []


def get_price_data_with_pykrx(ticker, start_date, end_date):
    """PyKRX를 사용해 가격 데이터 조회"""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        start_date_krx = start_dt.strftime("%Y%m%d")
        end_date_krx = end_dt.strftime("%Y%m%d")

        df = stock.get_market_ohlcv_by_date(start_date_krx, end_date_krx,
                                            ticker)

        if df.empty:
            return []

        df = df.reset_index()
        price_data = []

        for _, row in df.iterrows():
            price_data.append({
                "date": row["날짜"].date(),
                "open": float(row["시가"]),
                "high": float(row["고가"]),
                "low": float(row["저가"]),
                "close": float(row["종가"]),
                "volume": int(row["거래량"])
            })

        return sorted(price_data, key=lambda x: x["date"])

    except Exception as e:
        logger.warning(f"Failed to fetch PyKRX data for {ticker}: {e}")
        return []


def get_stock_data_from_db(conn, ticker, start_date, end_date):
    """DB에서 가격 데이터 조회 (백업용)"""
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT date, open_price, high_price, low_price, close_price, volume
                FROM daily_stock_data
                WHERE ticker = %s 
                AND date >= %s 
                AND date <= %s
                ORDER BY date ASC
            """
            cursor.execute(query, (ticker, start_date, end_date))
            results = cursor.fetchall()

            return [{
                "date": row[0],
                "open": float(row[1]) if row[1] else 0,
                "high": float(row[2]) if row[2] else 0,
                "low": float(row[3]) if row[3] else 0,
                "close": float(row[4]) if row[4] else 0,
                "volume": int(row[5]) if row[5] else 0
            } for row in results]

    except Exception as e:
        logger.warning(f"Failed to get DB data for {ticker}: {e}")
        return []


def simulate_k_value(price_data, k):
    """K 값 기반 시뮬레이션"""
    if len(price_data) < 2:
        return {
            "avg_return_pct": 0,
            "win_rate_pct": 0,
            "mdd_pct": 0,
            "trades": 0
        }

    returns = []
    wins = 0
    total_trades = 0

    for i in range(1, len(price_data)):
        prev_day = price_data[i - 1]
        today = price_data[i]

        if prev_day["high"] <= prev_day["low"]:
            continue

        daily_range = prev_day["high"] - prev_day["low"]
        target_price = today["open"] + (daily_range * k)

        if today["high"] >= target_price and target_price > today["open"]:
            return_pct = ((target_price - today["open"]) / today["open"]) * 100
            returns.append(return_pct)
            wins += 1
        else:
            if today["close"] > 0 and today["open"] > 0:
                return_pct = (
                    (today["close"] - today["open"]) / today["open"]) * 100
                returns.append(return_pct)

        total_trades += 1

    if not returns or total_trades == 0:
        return {
            "avg_return_pct": 0,
            "win_rate_pct": 0,
            "mdd_pct": 0,
            "trades": 0
        }

    avg_return = np.mean(returns)
    win_rate = (wins / total_trades) * 100

    # MDD 계산
    cumulative = [0]
    for ret in returns:
        cumulative.append(cumulative[-1] + ret)

    peak = cumulative[0]
    max_drawdown = 0
    for value in cumulative:
        if value > peak:
            peak = value
        drawdown = peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return {
        "avg_return_pct": float(avg_return),  # NumPy를 Python float로 변환
        "win_rate_pct": float(win_rate),
        "mdd_pct": float(max_drawdown),
        "trades": int(total_trades)
    }


def calculate_best_k_for_ticker(conn, ticker_info, start_date, end_date,
                                period_type):
    """개별 종목의 Best K 값 계산"""
    ticker = ticker_info["ticker"]
    name = ticker_info["name"]

    try:
        # 가격 데이터 조회
        price_data = get_price_data_with_pykrx(ticker, start_date, end_date)

        if not price_data:
            price_data = get_stock_data_from_db(conn, ticker, start_date,
                                                end_date)

        if len(price_data) < 5:
            logger.warning(
                f"[SKIP] {name}({ticker}) {period_type} - 데이터 부족 ({len(price_data)}일)"
            )
            return None

        # K 값들을 테스트 (0.1 ~ 0.9)
        k_results = []
        for k in np.arange(0.1, 1.0, 0.1):
            k = round(k, 1)
            metrics = simulate_k_value(price_data, k)

            avg_return = metrics["avg_return_pct"]
            mdd = max(metrics["mdd_pct"], 0.1)
            sharpe = avg_return / mdd if mdd > 0 else 0

            k_results.append({"k": k, "sharpe": sharpe, **metrics})

        if not k_results:
            return None

        best_result = max(k_results, key=lambda x: x["sharpe"])
        best_k = best_result["k"]

        # 음수 수익률 필터링
        if best_result["avg_return_pct"] <= 0:
            logger.debug(
                f"[FILTER] {name}({ticker}) {period_type} 수익률 {best_result['avg_return_pct']:.2f}% ≤ 0 → 제외"
            )
            return None

        result = {
            "ticker": ticker,
            "company_name": name,
            "period_type": period_type,
            "period_days": len(price_data),
            "best_k": float(best_k),  # NumPy float를 Python float로 변환
            "avg_return_pct": float(best_result["avg_return_pct"]),
            "win_rate_pct": float(best_result["win_rate_pct"]),
            "mdd_pct": float(best_result["mdd_pct"]),
            "total_trades": int(best_result["trades"]),
            "sharpe_ratio": float(best_result["sharpe"])
        }

        logger.info(f"[SUCCESS] {name}({ticker}) {period_type} K={best_k} "
                    f"R={result['avg_return_pct']:.1f}% "
                    f"W={result['win_rate_pct']:.1f}% "
                    f"MDD={result['mdd_pct']:.1f}% "
                    f"Trades={result['total_trades']}")

        return result

    except Exception as e:
        logger.error(
            f"[ERROR] {name}({ticker}) {period_type} Best K 계산 실패: {e}")
        return None


def insert_best_k_analysis(conn, result):
    """best_k_analysis 테이블에 결과 저장"""
    try:
        with conn.cursor() as cursor:
            conn.rollback()  # 에러 상태 초기화

            # 기존 데이터 삭제 (같은 종목, 같은 날짜, 같은 기간)
            delete_query = """
                DELETE FROM best_k_analysis 
                WHERE ticker = %s AND analysis_date = CURRENT_DATE AND period_type = %s
            """
            cursor.execute(delete_query,
                           (result["ticker"], result["period_type"]))

            # 새 데이터 삽입
            insert_query = """
                INSERT INTO best_k_analysis (
                    ticker, company_name, analysis_date, period_type, period_days,
                    best_k, avg_return_pct, win_rate_pct, mdd_pct, 
                    total_trades, sharpe_ratio
                ) VALUES (
                    %s, %s, CURRENT_DATE, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                )
            """

            cursor.execute(
                insert_query,
                (result["ticker"], result["company_name"],
                 result["period_type"], int(result["period_days"]),
                 float(result["best_k"]), float(result["avg_return_pct"]),
                 float(result["win_rate_pct"]), float(result["mdd_pct"]),
                 int(result["total_trades"]), float(result["sharpe_ratio"])))

            conn.commit()

    except Exception as e:
        logger.error(
            f"Failed to insert best_k_analysis for {result['ticker']}: {e}")
        conn.rollback()
        raise


def main():
    """메인 실행 함수"""
    try:
        input_data = json.loads(sys.stdin.read())

        period_type = input_data.get('period', 'month_1')
        start_date = input_data.get('startDate')
        end_date = input_data.get('endDate')
        market = input_data.get('market', 'ALL')

        logger.info(f"Best K 계산 시작 - 기간: {period_type}, 시장: {market}")

        # 기간 계산
        start_date_str, end_date_str = calculate_period_dates(
            period_type, start_date, end_date)
        logger.info(f"분석 기간: {start_date_str} ~ {end_date_str}")

        # 기간 타입 설정
        if period_type == "custom":
            db_period_type = "custom"  # 커스텀은 DB에 저장하지 않음
        else:
            db_period_type = PERIOD_CONFIG.get(period_type,
                                               {}).get("type", "month_1")

        # DB 연결
        conn = get_database_connection()
        if not conn:
            raise Exception("데이터베이스 연결 실패")

        # Top 200 종목 조회
        top_200_tickers = get_top_200_tickers(conn)
        if not top_200_tickers:
            raise Exception("Top 200 종목 조회 실패")

        # 시장 필터링
        if market and market != 'ALL':
            top_200_tickers = [
                t for t in top_200_tickers if t.get('market') == market
            ]

        logger.info(f"대상 종목 수: {len(top_200_tickers)}개, 기간: {db_period_type}")

        # 각 종목별 Best K 계산
        success_count = 0
        failed_count = 0
        filtered_count = 0

        for i, ticker_info in enumerate(top_200_tickers, 1):
            ticker = ticker_info["ticker"]
            name = ticker_info["name"]

            try:
                logger.info(
                    f"[{i}/{len(top_200_tickers)}] {name}({ticker}) 계산 시작")

                result = calculate_best_k_for_ticker(conn, ticker_info,
                                                     start_date_str,
                                                     end_date_str,
                                                     db_period_type)

                if result is None:
                    filtered_count += 1
                    continue

                # 커스텀 기간이 아닌 경우에만 DB 저장
                if period_type != "custom":
                    try:
                        insert_best_k_analysis(conn, result)
                        success_count += 1
                        logger.info(
                            f"[{i}/{len(top_200_tickers)}] {name}({ticker}) DB 저장 성공"
                        )
                    except Exception as db_error:
                        logger.error(
                            f"[{i}/{len(top_200_tickers)}] {name}({ticker}) DB 저장 실패: {db_error}"
                        )
                        failed_count += 1
                else:
                    success_count += 1  # 커스텀은 계산만 성공으로 처리

            except Exception as e:
                logger.error(
                    f"[{i}/{len(top_200_tickers)}] {name}({ticker}) 처리 실패: {e}"
                )
                failed_count += 1
                continue

        conn.close()

        # 결과 반환
        result_data = {
            "success": True,
            "message":
            f"Best K 계산 완료 ({db_period_type}) - 성공: {success_count}개, 실패: {failed_count}개, 필터링: {filtered_count}개",
            "data": {
                "updated_symbols": success_count,
                "failed_symbols": failed_count,
                "filtered_symbols": filtered_count,
                "total_symbols": len(top_200_tickers),
                "period": f"{start_date_str} ~ {end_date_str}",
                "period_type": db_period_type,
                "market": market or "ALL"
            }
        }

        logger.info(
            f"Best K 계산 완료 ({db_period_type}) - 성공: {success_count}/{len(top_200_tickers)}"
        )
        print(json.dumps(result_data, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.error(f"Best K 계산 전체 프로세스 실패: {e}")
        error_result = {
            "success": False,
            "message": f"Best K 계산 실패: {str(e)}",
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
