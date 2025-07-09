# MySQL 기반 일일 주식 데이터 수집 시스템

## 개요
매일 오전 8시에 자동으로 전일 주식 데이터를 수집하여 MySQL 데이터베이스에 저장하고, 5년치 데이터만 유지하는 시스템입니다.

## 주요 기능
- **자동 스케줄링**: 매일 오전 8시 KST에 자동 실행
- **실시간 데이터**: pykrx API를 사용하여 KOSPI/KOSDAQ 데이터 수집
- **데이터 보관**: 5년치 데이터만 유지하며 자동으로 오래된 데이터 삭제
- **상위 종목 선택**: 시가총액 기준 상위 500개 종목 (KOSPI 250개, KOSDAQ 250개)
- **로깅**: 상세한 실행 로그 및 오류 추적

## 파일 구조
```
server/services/
├── daily-stock-collector-mysql.py  # 메인 수집 스크립트
├── mysql-scheduler.ts              # Node.js 스케줄러 
├── mysql-schema.sql               # MySQL 테이블 스키마
├── test-mysql-collector.py       # 테스트 스크립트
└── README-mysql.md               # 사용법 가이드
```

## 환경 설정

### 1. 필요한 패키지 설치
```bash
# Python 패키지
pip install mysql-connector-python pykrx pandas

# Node.js 패키지  
npm install node-cron
```

### 2. 환경 변수 설정
```bash
export DB_HOST=localhost
export DB_NAME=stock_db
export DB_USER=root
export DB_PASSWORD=your_password
export DB_PORT=3306
```

### 3. MySQL 데이터베이스 설정
```bash
# MySQL 스키마 생성
mysql -u root -p < server/services/mysql-schema.sql
```

## 사용법

### 1. 자동 스케줄링 실행
```javascript
// Node.js 애플리케이션에서
import { mysqlScheduler } from './services/mysql-scheduler';

// 스케줄러 시작
mysqlScheduler.start();
```

### 2. 수동 실행
```bash
# Python 스크립트 직접 실행
python3 server/services/daily-stock-collector-mysql.py

# Node.js에서 수동 실행
mysqlScheduler.manualCollect();
```

### 3. 테스트 실행
```bash
# 테스트 스크립트 실행
python3 server/services/test-mysql-collector.py
```

## 데이터베이스 스키마

### stock_daily 테이블
```sql
PRIMARY KEY (date, code)  -- 복합 기본키
- date: 거래일자 (DATE)
- code: 종목코드 (VARCHAR(10))
- name: 종목명 (VARCHAR(100))
- open: 시가 (BIGINT)
- high: 고가 (BIGINT)
- low: 저가 (BIGINT)
- close: 종가 (BIGINT)
- volume: 거래량 (BIGINT)
- market_cap: 시가총액 (BIGINT)
```

### collection_log 테이블
```sql
- id: 로그 ID (AUTO_INCREMENT)
- collection_date: 수집 대상 날짜
- status: 수집 상태 (SUCCESS/FAILED/ERROR)
- total_records: 수집된 레코드 수
- execution_time: 실행 시간(초)
- error_message: 오류 메시지
```

## 모니터링

### 1. 실행 로그 확인
```bash
# 로그 파일 확인
tail -f /tmp/daily_stock_collector.log

# JSON 로그 확인
cat /tmp/mysql_collection_log.json
```

### 2. 데이터 현황 확인
```sql
-- 데이터 보관 현황 확인
SELECT * FROM data_retention_status;

-- 최근 수집 로그 확인
SELECT * FROM collection_log ORDER BY created_at DESC LIMIT 10;

-- 특정 종목 데이터 확인
SELECT * FROM stock_daily WHERE code = '005930' ORDER BY date DESC LIMIT 5;
```

## 특징

### 1. 5년 데이터 보관 정책
- 매일 실행 시 5년 이전 데이터 자동 삭제
- 데이터 무결성 검증 포함
- 디스크 사용량 최적화

### 2. 효율적 데이터 수집
- 시가총액 기준 상위 500개 종목만 수집
- 실패한 종목은 건너뛰고 계속 진행
- 병렬 처리로 성능 최적화

### 3. 강력한 오류 처리
- 네트워크 오류 시 재시도
- 상세한 로깅 및 오류 추적
- 부분 실패 시에도 수집 가능한 데이터는 저장

## 주의사항

1. **pykrx API 제한**: 너무 빠른 요청 시 차단될 수 있으므로 적절한 딜레이 필요
2. **데이터 정확성**: 공휴일이나 주말에는 데이터가 없을 수 있음
3. **데이터베이스 용량**: 5년치 데이터 약 500개 종목 기준 약 1GB 예상
4. **시간대**: 한국 시간 (KST) 기준으로 스케줄링

## 문제 해결

### 1. 데이터베이스 연결 오류
```bash
# MySQL 서비스 상태 확인
systemctl status mysql

# 연결 정보 확인
mysql -u root -p -e "SELECT 1"
```

### 2. pykrx 오류
```bash
# 패키지 업데이트
pip install --upgrade pykrx

# 의존성 확인
pip install pandas numpy
```

### 3. 스케줄러 오류
```bash
# Node.js 프로세스 확인
pm2 list

# 로그 확인
pm2 logs
```