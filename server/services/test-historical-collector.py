#!/usr/bin/env python3
"""
PostgreSQL 역사적 데이터 수집 테스트 스크립트
실제 API 호출로 최근 몇 일간의 데이터를 수집하여 테스트
"""

import sys
import os
from datetime import datetime, timedelta

# 현재 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_recent_data_collection():
    """최근 데이터 수집 테스트"""
    print("=== 최근 데이터 수집 테스트 ===")
    
    from historical_data_collector import get_ranking_lists, get_unique_tickers, get_stock_details, combine_data
    
    # 최근 평일 날짜 찾기 (주말 제외)
    test_date = datetime.now() - timedelta(days=1)
    while test_date.weekday() > 4:  # 주말 제외
        test_date -= timedelta(days=1)
    
    print(f"테스트 날짜: {test_date.strftime('%Y-%m-%d')}")
    
    # 1. 랭킹 리스트 수집
    ranking_data = get_ranking_lists(test_date)
    if ranking_data:
        print(f"랭킹 데이터 수집 성공: {len(ranking_data)}개")
        
        # 랭킹별 개수 확인
        kospi_cap = len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='market_cap'])
        kosdaq_cap = len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='market_cap'])
        kospi_vol = len([r for r in ranking_data if r['market']=='KOSPI' and r['rank_type']=='volume'])
        kosdaq_vol = len([r for r in ranking_data if r['market']=='KOSDAQ' and r['rank_type']=='volume'])
        
        print(f"  - KOSPI 시가총액: {kospi_cap}개")
        print(f"  - KOSDAQ 시가총액: {kosdaq_cap}개")
        print(f"  - KOSPI 거래량: {kospi_vol}개")
        print(f"  - KOSDAQ 거래량: {kosdaq_vol}개")
        
        # 2. 중복 제거
        unique_tickers = get_unique_tickers(ranking_data)
        print(f"중복 제거 후 종목 수: {len(unique_tickers)}개")
        
        # 3. 상세 데이터 수집 (처음 20개만 테스트)
        test_tickers = unique_tickers[:20]
        print(f"상세 데이터 수집 테스트: {len(test_tickers)}개")
        
        stock_details = get_stock_details(test_date, test_tickers)
        if stock_details:
            print(f"종목 상세 데이터 수집 성공: {len(stock_details)}개")
            
            # 4. 데이터 결합
            combined_data = combine_data(test_date, ranking_data[:80], stock_details)  # 랭킹 20개씩 4개 = 80개
            print(f"데이터 결합 성공: {len(combined_data)}개")
            
            # 샘플 데이터 출력
            print("\n샘플 데이터:")
            for i, item in enumerate(combined_data[:5]):
                print(f"  {i+1}. {item['symbol']} - {item['name']} ({item['market']} {item['rank_type']} {item['rank']}위)")
                print(f"     종가: {item['close_price']:,.0f}원, 거래량: {item['volume']:,}주")
            
            return True
        else:
            print("종목 상세 데이터 수집 실패")
            return False
    else:
        print("랭킹 데이터 수집 실패")
        return False

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n=== 데이터베이스 연결 테스트 ===")
    
    try:
        from historical_data_collector import get_database_connection, get_data_count
        
        conn = get_database_connection()
        count = get_data_count(conn)
        print(f"✅ PostgreSQL 연결 성공")
        print(f"현재 데이터 개수: {count:,}개")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False

def test_small_collection():
    """소규모 데이터 수집 테스트"""
    print("\n=== 소규모 데이터 수집 테스트 ===")
    
    from historical_data_collector import collect_historical_data
    
    # 최근 5일간 데이터 수집 테스트
    end_date = datetime.now() - timedelta(days=1)
    while end_date.weekday() > 4:  # 주말 제외
        end_date -= timedelta(days=1)
    
    start_date = end_date - timedelta(days=5)
    
    print(f"테스트 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    try:
        collect_historical_data(start_date, end_date)
        print("✅ 소규모 데이터 수집 완료")
        return True
    except Exception as e:
        print(f"❌ 소규모 데이터 수집 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("PostgreSQL 역사적 데이터 수집 테스트 시작")
    print("="*60)
    
    # 1. 데이터베이스 연결 테스트
    db_success = test_database_connection()
    
    # 2. 최근 데이터 수집 테스트
    api_success = test_recent_data_collection()
    
    # 3. 소규모 데이터 수집 테스트 (DB 연결과 API 모두 성공한 경우)
    if db_success and api_success:
        collection_success = test_small_collection()
    else:
        collection_success = False
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약:")
    print(f"  데이터베이스 연결: {'✅ 성공' if db_success else '❌ 실패'}")
    print(f"  API 데이터 수집: {'✅ 성공' if api_success else '❌ 실패'}")
    print(f"  소규모 데이터 수집: {'✅ 성공' if collection_success else '❌ 실패'}")
    
    if db_success and api_success and collection_success:
        print("\n🎉 모든 테스트 통과! 5년치 데이터 수집을 시작할 수 있습니다.")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 해결 후 다시 시도하세요.")

if __name__ == "__main__":
    main()