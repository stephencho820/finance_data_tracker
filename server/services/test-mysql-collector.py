#!/usr/bin/env python3
"""
MySQL 랭킹 데이터 수집 스크립트 테스트 실행
4개 랭킹 리스트 수집 및 중복 제거 기능 테스트
"""

import sys
import os
from datetime import datetime, timedelta

# 현재 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 설정 (테스트용)
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'stock_db' 
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = ''
os.environ['DB_PORT'] = '3306'

def test_ranking_lists():
    """랭킹 리스트 수집 함수 테스트"""
    print("=== 랭킹 리스트 수집 테스트 ===")
    
    # 테스트를 위해 함수 import
    from daily_stock_collector_mysql import get_ranking_lists
    
    # 어제 날짜로 테스트
    yesterday = datetime.now() - timedelta(days=1)
    
    print(f"테스트 날짜: {yesterday.strftime('%Y-%m-%d')}")
    
    # 랭킹 데이터 수집 시도
    ranking_data = get_ranking_lists(yesterday)
    
    if ranking_data:
        print(f"수집된 랭킹 데이터 개수: {len(ranking_data)}")
        
        # 랭킹별 개수 확인
        kospi_cap = len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='market_cap'])
        kosdaq_cap = len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='market_cap'])
        kospi_vol = len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='volume'])
        kosdaq_vol = len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='volume'])
        
        print(f"  - KOSPI 시가총액: {kospi_cap}개")
        print(f"  - KOSDAQ 시가총액: {kosdaq_cap}개")
        print(f"  - KOSPI 거래량: {kospi_vol}개")
        print(f"  - KOSDAQ 거래량: {kosdaq_vol}개")
        
        print("샘플 랭킹 데이터:")
        for i, item in enumerate(ranking_data[:5]):  # 처음 5개만 출력
            print(f"  {i+1}. {item['code']} - {item['market']} {item['rank_type']} {item['rank']}위")
    else:
        print("랭킹 데이터 수집 실패")

def test_unique_tickers():
    """중복 제거 함수 테스트"""
    print("\n=== 중복 제거 테스트 ===")
    
    from daily_stock_collector_mysql import get_ranking_lists, get_unique_tickers
    
    yesterday = datetime.now() - timedelta(days=1)
    ranking_data = get_ranking_lists(yesterday)
    
    if ranking_data:
        unique_tickers = get_unique_tickers(ranking_data)
        print(f"전체 랭킹 데이터: {len(ranking_data)}개")
        print(f"중복 제거 후 종목: {len(unique_tickers)}개")
        print(f"중복 제거율: {((len(ranking_data) - len(unique_tickers)) / len(ranking_data) * 100):.1f}%")
        
        print("샘플 종목 코드:")
        for i, ticker in enumerate(unique_tickers[:10]):  # 처음 10개만 출력
            print(f"  {i+1}. {ticker}")
    else:
        print("랭킹 데이터 없음")

def test_stock_details():
    """종목 상세 데이터 수집 테스트"""
    print("\n=== 종목 상세 데이터 수집 테스트 ===")
    
    from daily_stock_collector_mysql import get_stock_details
    
    yesterday = datetime.now() - timedelta(days=1)
    # 테스트용 종목 코드 (삼성전자, SK하이닉스, 네이버)
    test_tickers = ['005930', '000660', '035420']
    
    print(f"테스트 종목: {test_tickers}")
    
    stock_details = get_stock_details(yesterday, test_tickers)
    
    if stock_details:
        print(f"수집된 종목 상세 데이터: {len(stock_details)}개")
        for ticker, detail in stock_details.items():
            print(f"  {ticker} - {detail['name']}: {detail['close']:,}원")
    else:
        print("종목 상세 데이터 수집 실패")

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n=== 데이터베이스 연결 테스트 ===")
    
    try:
        from daily_stock_collector_mysql import get_database_connection
        
        conn = get_database_connection()
        print("✅ 데이터베이스 연결 성공")
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL 버전: {version[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")

def test_database_operations():
    """데이터베이스 CRUD 테스트"""
    print("\n=== 데이터베이스 CRUD 테스트 ===")
    
    try:
        from daily_stock_collector_mysql import get_database_connection, insert_daily_data, get_data_count
        
        conn = get_database_connection()
        
        # 현재 데이터 개수 확인
        initial_count = get_data_count(conn)
        print(f"현재 데이터 개수: {initial_count:,}개")
        
        # 테스트 데이터 생성
        test_data = [{
            'date': '2025-01-01',
            'code': 'TEST01',
            'market': 'KOSPI',
            'rank_type': 'market_cap',
            'rank': 1,
            'name': '테스트종목',
            'open': 10000,
            'high': 11000,
            'low': 9000,
            'close': 10500,
            'volume': 1000000,
            'market_cap': 1000000000
        }]
        
        # 데이터 삽입 테스트
        inserted = insert_daily_data(conn, test_data)
        print(f"테스트 데이터 삽입: {inserted}개")
        
        # 삽입 후 개수 확인
        after_count = get_data_count(conn)
        print(f"삽입 후 데이터 개수: {after_count:,}개")
        
        # 테스트 데이터 삭제
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stock_daily WHERE code = 'TEST01'")
        conn.commit()
        cursor.close()
        
        # 삭제 후 개수 확인
        final_count = get_data_count(conn)
        print(f"삭제 후 데이터 개수: {final_count:,}개")
        
        conn.close()
        print("✅ 데이터베이스 CRUD 테스트 완료")
        
    except Exception as e:
        print(f"❌ 데이터베이스 CRUD 테스트 실패: {e}")

def main():
    """메인 테스트 함수"""
    print("MySQL 랭킹 데이터 수집 스크립트 테스트 시작")
    print("="*60)
    
    # 1. 데이터베이스 연결 테스트
    test_database_connection()
    
    # 2. 랭킹 리스트 수집 테스트
    test_ranking_lists()
    
    # 3. 중복 제거 테스트
    test_unique_tickers()
    
    # 4. 종목 상세 데이터 수집 테스트
    test_stock_details()
    
    # 5. 데이터베이스 CRUD 테스트
    test_database_operations()
    
    print("\n테스트 완료")

if __name__ == "__main__":
    main()