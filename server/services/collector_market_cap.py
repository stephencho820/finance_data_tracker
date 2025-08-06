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
    """
    가장 최신의 완료된 거래일을 반환
    - 오후 4시 이전: 전 거래일
    - 오후 4시 이후: 당일이 거래일이면 당일, 아니면 가장 최근 거래일
    """
    now = datetime.now()

    # 시간 기준 결정
    market_closed = now.hour >= 16  # 오후 4시 이후면 장 마감으로 간주

    logger.info(
        f"⏰ 현재 시간: {now.strftime('%Y-%m-%d %H:%M')}, 장 마감 여부: {market_closed}")

    # 검색 시작점 결정
    if market_closed:
        # 장 마감 후: 오늘부터 확인
        check_date = start_date
        logger.info("📈 장 마감 후 - 오늘 데이터부터 확인")
    else:
        # 장 시간 중/이전: 어제부터 확인
        check_date = start_date - timedelta(days=1)
        logger.info("📊 장 시간 중 - 전 거래일부터 확인")

    # 최대 15일 전까지 거래일 탐색 (휴일 연휴 고려)
    for i in range(15):
        candidate_date = check_date - timedelta(days=i)
        date_str = candidate_date.strftime("%Y%m%d")

        try:
            logger.debug(f"🔍 {date_str} 거래일 여부 확인 중...")

            # PyKRX로 거래일 여부 확인
            nearest_business_day = stock.get_nearest_business_day_in_a_week(
                date_str)

            if nearest_business_day == date_str:
                # 해당 날짜가 거래일인 경우, 실제 데이터 존재 여부 확인
                try:
                    # 대표 종목(삼성전자)으로 데이터 존재 확인
                    test_df = stock.get_market_ohlcv(date_str, date_str,
                                                     "005930")

                    if not test_df.empty and len(test_df) > 0:
                        # 실제 거래 데이터가 있는 경우
                        row = test_df.iloc[0]
                        if row["종가"] > 0 and row["거래량"] > 0:
                            logger.info(
                                f"✅ 최신 거래일 확정: {candidate_date.strftime('%Y-%m-%d')} ({date_str})"
                            )
                            return candidate_date
                        else:
                            logger.debug(
                                f"⚠️ {date_str} - 데이터가 불완전함 (종가: {row['종가']}, 거래량: {row['거래량']})"
                            )
                    else:
                        logger.debug(f"⚠️ {date_str} - 거래 데이터 없음")

                except Exception as data_error:
                    logger.debug(f"⚠️ {date_str} - 데이터 조회 실패: {data_error}")

            else:
                logger.debug(
                    f"📅 {date_str} - 비거래일 (최근 거래일: {nearest_business_day})")

        except Exception as e:
            logger.debug(f"❌ {date_str} - 거래일 확인 실패: {e}")
            continue

    # 15일 내에 유효한 거래일을 찾지 못한 경우
    raise ValueError(
        f"📛 최근 15일 내 유효한 거래일을 찾을 수 없습니다 (기준: {start_date.strftime('%Y-%m-%d')})"
    )


def get_top_200_by_market_cap(date: datetime):
    """시가총액 기준 Top 200 종목 수집 (KOSPI + KOSDAQ 통합)"""
    date_str = date.strftime("%Y%m%d")
    logger.info(f"📥 {date_str} 기준 시총 Top 200 수집 시작")

    try:
        # KOSPI 시가총액 수집
        logger.info("📊 KOSPI 시가총액 수집 중...")
        cap_kospi = stock.get_market_cap_by_ticker(date_str, market="KOSPI")
        if not cap_kospi.empty:
            cap_kospi["market"] = "KOSPI"
            cap_kospi = cap_kospi.reset_index()
            cap_kospi = cap_kospi.rename(columns={
                "티커": "ticker",
                "시가총액": "market_cap"
            })
        else:
            cap_kospi = pd.DataFrame(
                columns=["ticker", "market_cap", "market"])

        # KOSDAQ 시가총액 수집
        logger.info("📊 KOSDAQ 시가총액 수집 중...")
        cap_kosdaq = stock.get_market_cap_by_ticker(date_str, market="KOSDAQ")
        if not cap_kosdaq.empty:
            cap_kosdaq["market"] = "KOSDAQ"
            cap_kosdaq = cap_kosdaq.reset_index()
            cap_kosdaq = cap_kosdaq.rename(columns={
                "티커": "ticker",
                "시가총액": "market_cap"
            })
        else:
            cap_kosdaq = pd.DataFrame(
                columns=["ticker", "market_cap", "market"])

        # 데이터 통합
        all_caps = pd.concat([cap_kospi, cap_kosdaq], ignore_index=True)

        if all_caps.empty:
            logger.error("❌ 시가총액 데이터 수집 실패")
            return []

        # 시가총액 기준 Top 200 선택
        top_200 = all_caps.nlargest(200, "market_cap")

        logger.info(f"🧾 총 종목 수: {len(all_caps)}, Top 200 선택 완료")
        logger.info(
            f"📈 KOSPI: {len(top_200[top_200['market'] == 'KOSPI'])}개, KOSDAQ: {len(top_200[top_200['market'] == 'KOSDAQ'])}개"
        )

        return top_200.to_dict('records')

    except Exception as e:
        logger.error(f"❌ 시가총액 수집 실패: {e}")
        return []


def get_market_data(date: datetime):
    """시가총액 Top 200 종목의 상세 정보 수집"""
    # Top 200 종목 선정
    top_200_list = get_top_200_by_market_cap(date)

    if not top_200_list:
        logger.error("❌ Top 200 종목 선정 실패")
        return []

    date_str = date.strftime("%Y%m%d")
    total_tickers = len(top_200_list)

    logger.info(f"📊 Top {total_tickers}개 종목 상세 정보 수집 시작...")

    rows = []
    failed_count = 0

    for i, ticker_info in enumerate(top_200_list, 1):
        ticker = str(ticker_info["ticker"]).zfill(6)  # 6자리 패딩
        market = ticker_info["market"]
        market_cap = ticker_info["market_cap"]

        try:
            # 진행률 출력 (API에서 추적하는 형태)
            logger.info(f"[{i}/{total_tickers}] {ticker} ({market}) 수집 중...")

            # 종목명 조회
            try:
                company_name = stock.get_market_ticker_name(ticker)
            except:
                company_name = f"종목{ticker}"

            # OHLCV 데이터 조회
            try:
                df = stock.get_market_ohlcv(date_str, date_str, ticker)
                if df.empty:
                    logger.warning(f"⚠️ {ticker} OHLCV 데이터 없음")
                    failed_count += 1
                    continue

                row = df.iloc[0]
                ohlcv = {
                    "open": int(row["시가"]) if row["시가"] > 0 else 0,
                    "high": int(row["고가"]) if row["고가"] > 0 else 0,
                    "low": int(row["저가"]) if row["저가"] > 0 else 0,
                    "close": int(row["종가"]) if row["종가"] > 0 else 0,
                    "volume": int(row["거래량"]) if row["거래량"] > 0 else 0,
                }

                # 데이터 검증
                if ohlcv["close"] <= 0:
                    logger.warning(f"⚠️ {ticker} 유효하지 않은 종가")
                    failed_count += 1
                    continue

            except Exception as e:
                logger.warning(f"⚠️ {ticker} OHLCV 조회 실패: {e}")
                failed_count += 1
                continue

            # 최종 데이터 구성
            row_data = {
                "date": date.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "name": company_name,
                "market": market,
                "market_cap": int(market_cap),
                "open_price": ohlcv["open"],
                "high_price": ohlcv["high"],
                "low_price": ohlcv["low"],
                "close_price": ohlcv["close"],
                "volume": ohlcv["volume"],
            }

            rows.append(row_data)

            # 주기적 진행 상황 출력
            if i % 50 == 0:
                logger.info(
                    f"✅ 진행률: {i}/{total_tickers} ({(i/total_tickers)*100:.1f}%) - 성공: {len(rows)}개, 실패: {failed_count}개"
                )

        except Exception as e:
            logger.error(f"❌ {ticker} 처리 실패: {e}")
            failed_count += 1
            continue

    logger.info(f"✅ 수집 완료 - 성공: {len(rows)}개, 실패: {failed_count}개")
    return rows


def insert_data(conn, rows):
    """데이터베이스에 데이터 삽입"""
    if not rows:
        logger.warning("❗ 삽입할 데이터 없음")
        return

    try:
        with conn.cursor() as cur:
            # 기존 데이터 삭제 (전체 초기화)
            logger.info("🗑️ 기존 daily_market_cap 데이터 삭제 중...")
            cur.execute("DELETE FROM daily_market_cap;")

            # 새 데이터 삽입
            logger.info(f"📌 {len(rows)}개 종목 데이터 삽입 중...")
            sql = """
                INSERT INTO daily_market_cap
                (date, ticker, name, market, market_cap,
                 open_price, high_price, low_price, close_price, volume)
                VALUES (%(date)s, %(ticker)s, %(name)s, %(market)s, %(market_cap)s,
                        %(open_price)s, %(high_price)s, %(low_price)s, 
                        %(close_price)s, %(volume)s)
            """
            execute_batch(cur, sql, rows, page_size=100)
            conn.commit()

        logger.info(f"✅ {len(rows)}개 종목 데이터 삽입 완료")

        # 삽입 결과 검증
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM daily_market_cap WHERE date = %s",
                (rows[0]["date"], ))
            inserted_count = cur.fetchone()[0]
            logger.info(f"📊 검증: DB에 {inserted_count}개 종목 저장 확인")

    except Exception as e:
        logger.error(f"❌ 데이터 삽입 실패: {e}")
        conn.rollback()
        raise


# 메인 함수도 약간 수정
def main():
    try:
        logger.info("🚀 시가총액 Top 200 수집 시작")

        # 최신 거래일 확인 (스마트 로직 적용)
        latest_date = get_latest_trading_day(datetime.now())
        logger.info(f"📅 수집 대상 날짜: {latest_date.strftime('%Y-%m-%d')}")

        # 주말이나 휴일인 경우 추가 안내
        today = datetime.now().date()
        if latest_date.date() != today:
            days_diff = (today - latest_date.date()).days
            logger.info(f"💡 최신 거래일은 {days_diff}일 전입니다 (휴장일 제외)")

        # 데이터 수집
        rows = get_market_data(latest_date)

        if not rows:
            logger.error("❌ 수집된 데이터 없음")
            sys.exit(1)

        if len(rows) < 50:
            logger.warning(f"⚠️ 수집된 종목 수가 적음: {len(rows)}개 (최소 50개 권장)")

        # 데이터베이스 저장
        conn = get_db()
        insert_data(conn, rows)
        conn.close()

        logger.info(
            f"🎯 시가총액 수집 완료 - 총 {len(rows)}개 종목 ({latest_date.strftime('%Y-%m-%d')} 기준)"
        )

    except Exception as e:
        logger.error(f"🚨 전체 프로세스 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
