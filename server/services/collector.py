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


def get_market_cap_tickers(conn):
    """daily_market_cap 테이블에서 최신 종목 목록 조회"""
    try:
        with conn.cursor() as cur:
            query = """
                SELECT ticker, name, market
                FROM daily_market_cap
                WHERE date = (SELECT MAX(date) FROM daily_market_cap)
                ORDER BY market_cap::numeric DESC
            """
            cur.execute(query)
            rows = cur.fetchall()

            tickers_info = []
            for row in rows:
                tickers_info.append({
                    "ticker": row[0],
                    "name": row[1],
                    "market": row[2]
                })

            logger.info(f"📊 daily_market_cap에서 {len(tickers_info)}개 종목 조회")
            return tickers_info

    except Exception as e:
        logger.error(f"❌ 종목 목록 조회 실패: {e}")
        return []


def check_market_cap_dependency(conn):
    """시가총액 수집 완료 여부 확인"""
    try:
        with conn.cursor() as cur:
            today = datetime.now().date()
            query = """
                SELECT COUNT(*) as count, MAX(date) as latest_date
                FROM daily_market_cap
                WHERE date = %s
            """
            cur.execute(query, (today, ))
            result = cur.fetchone()

            count = result[0] if result else 0
            latest_date = result[1] if result else None

            if count < 50:  # 최소 50개 종목 필요
                logger.error(f"❌ 시가총액 데이터 부족: {count}개 (최소 50개 필요)")
                logger.error("💡 먼저 시가총액 수집을 실행해주세요")
                return False

            logger.info(f"✅ 시가총액 데이터 확인: {count}개 종목 ({latest_date})")
            return True

    except Exception as e:
        logger.error(f"❌ 의존성 확인 실패: {e}")
        return False


def get_latest_working_day():
    """최신 거래일 확인"""
    today = datetime.today().date()
    for i in range(0, 10):
        date = today - timedelta(days=i)
        try:
            # 삼성전자로 거래일 확인
            if not stock.get_market_ohlcv_by_date(date.strftime("%Y%m%d"),
                                                  date.strftime("%Y%m%d"),
                                                  "005930").empty:
                return date
        except:
            continue
    raise Exception("최근 거래일을 찾을 수 없습니다.")


def fetch_ohlcv_for_ticker(ticker, ticker_name, start_date, end_date):
    """개별 종목의 OHLCV 데이터 수집"""
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        if df is None or df.empty:
            logger.warning(f"⚠️ {ticker_name}({ticker}) - 데이터 없음")
            return []

        df = df.reset_index()
        rows = []

        for _, row in df.iterrows():
            # 데이터 유효성 검사
            if row["종가"] <= 0 or row["거래량"] < 0:
                continue

            rows.append({
                "date":
                row["날짜"].strftime("%Y-%m-%d"),
                "ticker":
                ticker,
                "open_price":
                float(row["시가"]) if row["시가"] > 0 else float(row["종가"]),
                "high_price":
                float(row["고가"]) if row["고가"] > 0 else float(row["종가"]),
                "low_price":
                float(row["저가"]) if row["저가"] > 0 else float(row["종가"]),
                "close_price":
                float(row["종가"]),
                "volume":
                int(row["거래량"]),
            })

        logger.debug(f"✅ {ticker_name}({ticker}) - {len(rows)}일 데이터 수집")
        return rows

    except Exception as e:
        logger.warning(f"❌ {ticker_name}({ticker}) OHLCV 수집 실패: {e}")
        return []


def insert_ohlcv_batch(conn, rows):
    """OHLCV 데이터 배치 삽입"""
    if not rows:
        return 0

    try:
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
                volume = EXCLUDED.volume
        """

        with conn.cursor() as cur:
            execute_batch(cur, query, rows, page_size=1000)
        conn.commit()

        return len(rows)

    except Exception as e:
        logger.error(f"❌ 데이터 삽입 실패: {e}")
        conn.rollback()
        return 0


def update_market_cap_with_latest_ohlcv(conn, latest_ohlcv_rows):
    """daily_market_cap 테이블에 최신 OHLCV 업데이트"""
    if not latest_ohlcv_rows:
        logger.warning("⚠️ 업데이트할 최신 OHLCV 데이터 없음")
        return

    try:
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
            execute_batch(cur, query, latest_ohlcv_rows, page_size=200)
        conn.commit()

        logger.info(
            f"✅ daily_market_cap에 {len(latest_ohlcv_rows)}개 종목 OHLCV 업데이트 완료")

    except Exception as e:
        logger.error(f"❌ daily_market_cap 업데이트 실패: {e}")
        conn.rollback()


def clean_old_data(conn, cutoff_date):
    """1년 이상 된 오래된 데이터 정리 (Queue 형태 유지)"""
    try:
        with conn.cursor() as cur:
            # 삭제 전 데이터 확인
            cur.execute(
                "SELECT COUNT(*) FROM daily_stock_data WHERE date < %s",
                (cutoff_date, ))
            old_count = cur.fetchone()[0]

            if old_count > 0:
                logger.info(f"🗑️ {cutoff_date} 이전 데이터 {old_count:,}개 삭제 중...")
                cur.execute("DELETE FROM daily_stock_data WHERE date < %s",
                            (cutoff_date, ))
                conn.commit()
                logger.info(f"✅ 오래된 데이터 정리 완료")
            else:
                logger.info("📊 정리할 오래된 데이터 없음")

    except Exception as e:
        logger.error(f"❌ 데이터 정리 실패: {e}")
        conn.rollback()


def main():
    start_time = time.time()
    logger.info("🚀 1년치 주식 데이터 수집 시작")

    try:
        # 데이터베이스 연결
        conn = get_db_connection()

        # 1. 의존성 확인 (시가총액 수집 완료 여부)
        if not check_market_cap_dependency(conn):
            logger.error("❌ 시가총액 수집이 완료되지 않음")
            sys.exit(1)

        # 2. 대상 종목 조회
        tickers_info = get_market_cap_tickers(conn)
        if not tickers_info:
            logger.error("❌ 수집 대상 종목 없음")
            sys.exit(1)

        # 3. 수집 기간 설정
        end_date_obj = get_latest_working_day()
        start_date_obj = end_date_obj - timedelta(days=400)  # 여유있게 400일

        start_date = start_date_obj.strftime("%Y%m%d")
        end_date = end_date_obj.strftime("%Y%m%d")
        target_date_str = end_date_obj.strftime("%Y-%m-%d")

        logger.info(f"📅 수집 기간: {start_date} ~ {end_date}")
        logger.info(f"🎯 최신 거래일: {target_date_str}")
        logger.info(f"📊 대상 종목 수: {len(tickers_info)}개")

        # 4. 데이터 수집 시작
        total_inserted = 0
        success_count = 0
        failed_count = 0
        latest_ohlcv_rows = []

        for i, ticker_info in enumerate(tickers_info, 1):
            ticker = ticker_info["ticker"]
            ticker_name = ticker_info["name"]
            market = ticker_info["market"]

            # 진행률 출력 (API에서 추적하는 형태)
            logger.info(
                f"[{i}/{len(tickers_info)}] {ticker_name}({ticker}) [{market}] 수집 시작"
            )

            try:
                # OHLCV 데이터 수집
                rows = fetch_ohlcv_for_ticker(ticker, ticker_name, start_date,
                                              end_date)

                if not rows:
                    failed_count += 1
                    continue

                # 데이터베이스 삽입
                inserted = insert_ohlcv_batch(conn, rows)
                total_inserted += inserted
                success_count += 1

                # 최신 데이터 추출 (daily_market_cap 업데이트용)
                latest_row = next(
                    (r for r in rows if r["date"] == target_date_str), None)
                if latest_row:
                    latest_ohlcv_rows.append(latest_row)

                logger.info(
                    f"✅ {ticker_name}({ticker}) - {inserted:,}개 데이터 저장")

                # 주기적 진행 상황 출력
                if i % 20 == 0:
                    progress_pct = (i / len(tickers_info)) * 100
                    logger.info(
                        f"📈 진행률: {progress_pct:.1f}% - 성공: {success_count}개, 실패: {failed_count}개"
                    )

                # API 호출 제한 고려 (1초 대기)
                time.sleep(1)

            except Exception as e:
                logger.error(f"❌ {ticker_name}({ticker}) 처리 실패: {e}")
                failed_count += 1
                continue

        # 5. daily_market_cap 테이블 OHLCV 업데이트
        logger.info("📊 daily_market_cap 테이블 OHLCV 업데이트 중...")
        update_market_cap_with_latest_ohlcv(conn, latest_ohlcv_rows)

        # 6. 오래된 데이터 정리 (1년 이상 된 데이터)
        cutoff_date = end_date_obj - timedelta(days=400)
        clean_old_data(conn, cutoff_date)

        # 7. 최종 통계 확인
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(DISTINCT ticker) as ticker_count, COUNT(*) as total_rows FROM daily_stock_data WHERE date >= %s",
                (start_date_obj, ))
            stats = cur.fetchone()
            final_ticker_count = stats[0]
            final_total_rows = stats[1]

        conn.close()

        # 8. 결과 출력
        elapsed_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("🎯 1년치 주식 데이터 수집 완료")
        logger.info(f"📊 처리 종목: {len(tickers_info)}개")
        logger.info(f"✅ 성공: {success_count}개, ❌ 실패: {failed_count}개")
        logger.info(f"💾 총 저장 데이터: {total_inserted:,}개")
        logger.info(f"📈 DB 최종 종목 수: {final_ticker_count}개")
        logger.info(f"📈 DB 최종 데이터 수: {final_total_rows:,}개")
        logger.info(f"⏱️ 소요 시간: {elapsed_time:.1f}초")
        logger.info("=" * 60)

        # 성공률 체크
        success_rate = (success_count / len(tickers_info)) * 100
        if success_rate < 80:
            logger.warning(f"⚠️ 성공률이 낮습니다: {success_rate:.1f}%")

    except Exception as e:
        logger.error(f"🚨 전체 프로세스 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
