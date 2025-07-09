#!/usr/bin/env python3
"""
Best k값 계산 알고리즘
특정 알고리즘을 통해 종목별 Best k값을 계산하여 데이터베이스에 저장
"""

import sys
import json
import traceback
import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import math

def get_database_connection():
    """데이터베이스 연결 설정"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            database=os.getenv('PGDATABASE'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            port=os.getenv('PGPORT', 5432)
        )
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}", file=sys.stderr)
        return None

def get_stock_data(conn, start_date, end_date, market=None, limit=None):
    """데이터베이스에서 주식 데이터 조회"""
    try:
        cursor = conn.cursor()
        
        # 쿼리 구성
        query = """
        SELECT symbol, name, date, open_price, high_price, low_price, close_price, volume, market_cap, market
        FROM daily_stock_data
        WHERE date >= %s AND date <= %s
        """
        params = [start_date, end_date]
        
        if market:
            query += " AND market = %s"
            params.append(market)
        
        query += " ORDER BY symbol, date"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # DataFrame으로 변환
        columns = ['symbol', 'name', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume', 'market_cap', 'market']
        df = pd.DataFrame(results, columns=columns)
        
        cursor.close()
        return df
        
    except Exception as e:
        print(f"[ERROR] Failed to get stock data: {e}", file=sys.stderr)
        return pd.DataFrame()

def calculate_technical_indicators(df):
    """기술적 지표 계산"""
    try:
        # 가격 변동률 계산
        df['price_change'] = df['close_price'].pct_change()
        
        # 이동평균 계산 (5일, 20일, 60일)
        df['ma_5'] = df['close_price'].rolling(window=5).mean()
        df['ma_20'] = df['close_price'].rolling(window=20).mean()
        df['ma_60'] = df['close_price'].rolling(window=60).mean()
        
        # RSI 계산
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        df['rsi'] = calculate_rsi(df['close_price'])
        
        # 변동성 계산 (20일 표준편차)
        df['volatility'] = df['price_change'].rolling(window=20).std()
        
        # 거래량 이동평균
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        return df
        
    except Exception as e:
        print(f"[ERROR] Technical indicators calculation failed: {e}", file=sys.stderr)
        return df

def calculate_best_k_value(stock_data):
    """Best k값 계산 알고리즘"""
    try:
        # 최신 데이터가 충분하지 않으면 기본값 반환
        if len(stock_data) < 60:
            return 0.5
        
        # 최근 60일 데이터 사용
        recent_data = stock_data.tail(60).copy()
        
        # 기술적 지표 계산
        recent_data = calculate_technical_indicators(recent_data)
        
        # Best k값 계산을 위한 다중 요소 분석
        factors = []
        
        # 1. 가격 모멘텀 (20%)
        price_momentum = recent_data['price_change'].tail(20).mean()
        momentum_score = max(0, min(1, (price_momentum + 0.1) / 0.2))
        factors.append(momentum_score * 0.2)
        
        # 2. 이동평균 교차 신호 (25%)
        ma_cross_score = 0
        if not recent_data['ma_5'].isna().all() and not recent_data['ma_20'].isna().all():
            if recent_data['ma_5'].iloc[-1] > recent_data['ma_20'].iloc[-1]:
                ma_cross_score += 0.6
            if recent_data['ma_20'].iloc[-1] > recent_data['ma_60'].iloc[-1]:
                ma_cross_score += 0.4
        factors.append(ma_cross_score * 0.25)
        
        # 3. RSI 기반 과매수/과매도 분석 (15%)
        rsi_score = 0
        if not recent_data['rsi'].isna().all():
            latest_rsi = recent_data['rsi'].iloc[-1]
            if 30 <= latest_rsi <= 70:  # 적정 구간
                rsi_score = 0.8
            elif latest_rsi < 30:  # 과매도
                rsi_score = 0.9
            else:  # 과매수
                rsi_score = 0.3
        factors.append(rsi_score * 0.15)
        
        # 4. 변동성 분석 (20%)
        volatility_score = 0
        if not recent_data['volatility'].isna().all():
            avg_volatility = recent_data['volatility'].mean()
            # 적정 변동성 구간 (0.02 ~ 0.05)
            if 0.02 <= avg_volatility <= 0.05:
                volatility_score = 0.8
            elif avg_volatility < 0.02:
                volatility_score = 0.6  # 너무 낮은 변동성
            else:
                volatility_score = max(0.2, 0.8 - (avg_volatility - 0.05) * 5)
        factors.append(volatility_score * 0.2)
        
        # 5. 거래량 분석 (20%)
        volume_score = 0
        if not recent_data['volume_ma'].isna().all():
            recent_volume = recent_data['volume'].tail(5).mean()
            avg_volume = recent_data['volume_ma'].iloc[-1]
            if avg_volume > 0:
                volume_ratio = recent_volume / avg_volume
                if volume_ratio > 1.2:  # 거래량 증가
                    volume_score = 0.8
                elif volume_ratio > 0.8:  # 정상 거래량
                    volume_score = 0.6
                else:  # 거래량 감소
                    volume_score = 0.4
        factors.append(volume_score * 0.2)
        
        # 최종 Best k값 계산
        best_k = sum(factors)
        
        # 시장 상황에 따른 조정
        market_adjustment = 0
        if not recent_data['price_change'].isna().all():
            market_trend = recent_data['price_change'].tail(10).mean()
            if market_trend > 0.02:  # 강한 상승 추세
                market_adjustment = 0.1
            elif market_trend < -0.02:  # 강한 하락 추세
                market_adjustment = -0.1
        
        best_k = max(0.1, min(0.9, best_k + market_adjustment))
        
        return round(best_k, 4)
        
    except Exception as e:
        print(f"[ERROR] Best k calculation failed: {e}", file=sys.stderr)
        return 0.5

def update_best_k_values(conn, start_date, end_date, market=None):
    """Best k값 계산 및 업데이트"""
    try:
        # 주식 데이터 조회
        print(f"[INFO] Fetching stock data for best k calculation...", file=sys.stderr)
        df = get_stock_data(conn, start_date, end_date, market)
        
        if df.empty:
            print(f"[WARNING] No stock data found for the period", file=sys.stderr)
            return 0
        
        # 종목별로 그룹화
        grouped = df.groupby('symbol')
        updated_count = 0
        
        cursor = conn.cursor()
        
        for symbol, stock_data in grouped:
            try:
                # Best k값 계산
                best_k = calculate_best_k_value(stock_data)
                
                # 데이터베이스 업데이트
                update_query = """
                UPDATE daily_stock_data 
                SET best_k_value = %s
                WHERE symbol = %s AND date >= %s AND date <= %s
                """
                
                cursor.execute(update_query, (best_k, symbol, start_date, end_date))
                updated_count += 1
                
                if updated_count % 10 == 0:
                    print(f"[INFO] Updated best k values for {updated_count} symbols", file=sys.stderr)
                    
            except Exception as e:
                print(f"[WARNING] Failed to calculate best k for {symbol}: {e}", file=sys.stderr)
                continue
        
        conn.commit()
        cursor.close()
        
        return updated_count
        
    except Exception as e:
        print(f"[ERROR] Best k update failed: {e}", file=sys.stderr)
        return 0

def main():
    """메인 실행 함수"""
    try:
        # 입력 파라미터 파싱
        input_data = json.loads(sys.stdin.read())
        start_date = input_data.get('startDate')
        end_date = input_data.get('endDate')
        market = input_data.get('market')
        
        print(f"[INFO] Starting best k calculation for {market}", file=sys.stderr)
        print(f"[INFO] Period: {start_date} to {end_date}", file=sys.stderr)
        
        # 데이터베이스 연결
        conn = get_database_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        # Best k값 계산 및 업데이트
        updated_count = update_best_k_values(conn, start_date, end_date, market)
        
        conn.close()
        
        # 결과 반환
        print(json.dumps({
            'success': True,
            'message': f'Successfully calculated best k values for {updated_count} symbols',
            'data': {
                'updated_symbols': updated_count,
                'period': f'{start_date} to {end_date}',
                'market': market
            }
        }))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'message': f'Best k calculation failed: {str(e)}',
            'traceback': traceback.format_exc()
        }))

if __name__ == "__main__":
    main()