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
    market ENUM('KOSPI', 'KOSDAQ') NOT NULL COMMENT '시장구분',
    rank_type ENUM('market_cap', 'volume') NOT NULL COMMENT '랭킹구분',
    rank INT NOT NULL COMMENT '순위',
    name VARCHAR(100) NOT NULL COMMENT '종목명',
    open BIGINT NOT NULL DEFAULT 0 COMMENT '시가',
    high BIGINT NOT NULL DEFAULT 0 COMMENT '고가',
    low BIGINT NOT NULL DEFAULT 0 COMMENT '저가',
    close BIGINT NOT NULL DEFAULT 0 COMMENT '종가',
    volume BIGINT NOT NULL DEFAULT 0 COMMENT '거래량',
    market_cap BIGINT NOT NULL DEFAULT 0 COMMENT '시가총액',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    -- 복합 기본키 (날짜, 종목코드, 시장구분, 랭킹구분)
    PRIMARY KEY (date, code, market, rank_type),
    
    -- 인덱스 생성
    INDEX idx_date (date),
    INDEX idx_code (code),
    INDEX idx_market (market),
    INDEX idx_rank_type (rank_type),
    INDEX idx_rank (rank),
    INDEX idx_market_cap (market_cap DESC),
    INDEX idx_volume (volume DESC),
    INDEX idx_market_rank (market, rank_type, rank),
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
    COUNT(DISTINCT CONCAT(market, '_', rank_type)) as ranking_types,
    DATEDIFF(MAX(date), MIN(date)) as retention_days
FROM stock_daily;

-- 랭킹별 데이터 현황 뷰
CREATE OR REPLACE VIEW ranking_summary AS
SELECT 
    date,
    market,
    rank_type,
    COUNT(*) as stock_count,
    AVG(rank) as avg_rank,
    MIN(rank) as min_rank,
    MAX(rank) as max_rank
FROM stock_daily
GROUP BY date, market, rank_type
ORDER BY date DESC, market, rank_type;

-- 종목별 랭킹 포함 현황 뷰
CREATE OR REPLACE VIEW stock_ranking_status AS
SELECT 
    date,
    code,
    name,
    GROUP_CONCAT(CONCAT(market, '_', rank_type, '(', rank, ')') ORDER BY market, rank_type) as rankings,
    COUNT(*) as ranking_count
FROM stock_daily
GROUP BY date, code, name
ORDER BY date DESC, code;