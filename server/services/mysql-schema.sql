-- MySQL 데이터베이스 및 테이블 스키마
-- 5년치 일일 주식 데이터 저장용

-- 데이터베이스 생성 (필요한 경우)
CREATE DATABASE IF NOT EXISTS stock_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE stock_db;

-- 일일 주식 데이터 테이블
CREATE TABLE IF NOT EXISTS stock_daily (
    date DATE NOT NULL COMMENT '거래일자',
    code VARCHAR(10) NOT NULL COMMENT '종목코드',
    name VARCHAR(100) NOT NULL COMMENT '종목명',
    open BIGINT NOT NULL DEFAULT 0 COMMENT '시가',
    high BIGINT NOT NULL DEFAULT 0 COMMENT '고가',
    low BIGINT NOT NULL DEFAULT 0 COMMENT '저가',
    close BIGINT NOT NULL DEFAULT 0 COMMENT '종가',
    volume BIGINT NOT NULL DEFAULT 0 COMMENT '거래량',
    market_cap BIGINT NOT NULL DEFAULT 0 COMMENT '시가총액',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    -- 복합 기본키 (날짜, 종목코드)
    PRIMARY KEY (date, code),
    
    -- 인덱스 생성
    INDEX idx_date (date),
    INDEX idx_code (code),
    INDEX idx_market_cap (market_cap DESC),
    INDEX idx_volume (volume DESC),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci 
COMMENT='일일 주식 데이터';

-- 데이터 수집 로그 테이블
CREATE TABLE IF NOT EXISTS collection_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    collection_date DATE NOT NULL COMMENT '수집 대상 날짜',
    status ENUM('SUCCESS', 'FAILED', 'ERROR') NOT NULL COMMENT '수집 상태',
    total_records INT NOT NULL DEFAULT 0 COMMENT '수집된 레코드 수',
    execution_time DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '실행 시간(초)',
    error_message TEXT COMMENT '오류 메시지',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    
    INDEX idx_collection_date (collection_date),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci 
COMMENT='데이터 수집 로그';

-- 데이터 보관 정책 확인용 뷰
CREATE OR REPLACE VIEW data_retention_status AS
SELECT 
    DATE(MIN(date)) as earliest_date,
    DATE(MAX(date)) as latest_date,
    COUNT(*) as total_records,
    COUNT(DISTINCT code) as unique_stocks,
    DATEDIFF(MAX(date), MIN(date)) as retention_days
FROM stock_daily;