#!/usr/bin/env python3
"""
MySQL 데이터 수집 스크립트 테스트 실행
개발 환경에서 스크립트 동작 확인용
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

def test_get_market_data():
    """get_market_data 함수 테스트"""
    print("=== get_market_data 함수 테스트 ===")
    
    # 테스트를 위해 함수 import
    from daily_stock_collector_mysql import get_market_data
    
    # 어제 날짜로 테스트
    yesterday = datetime.now() - timedelta(days=1)
    
    print(f"테스트 날짜: {yesterday.strftime('%Y-%m-%d')}")
    
    # 데이터 수집 시도
    data = get_market_data(yesterday)
    
    if data:
        print(f"수집된 데이터 개수: {len(data)}")
        print("샘플 데이터:")
        for i, item in enumerate(data[:3]):  # 처음 3개만 출력
            print(f"  {i+1}. {item['code']} - {item['name']}: {item['close']:,}원")
    else:
        print("데이터 수집 실패")

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

def main():
    """메인 테스트 함수"""
    print("MySQL 데이터 수집 스크립트 테스트 시작")
    print("="*50)
    
    # 1. 데이터베이스 연결 테스트
    test_database_connection()
    
    # 2. 시장 데이터 수집 테스트
    test_get_market_data()
    
    print("\n테스트 완료")

if __name__ == "__main__":
    main()