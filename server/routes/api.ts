// ✅ server/routes/api.ts
import { Router } from "express";
import { spawn } from "child_process";
import pg from "pg"; // ✅ PostgreSQL 연결 추가

const { Pool } = pg;
const router = Router();

// ✅ 진행률 상태 저장 객체
const dataCollectionProgress = {
  current: 0,
  total: 200,
};

// ✅ Best K 계산 진행률 상태
const bestKProgress = {
  current: 0,
  total: 200,
  isRunning: false,
};

// ✅ PostgreSQL 연결 풀
const pool = new Pool({
  host: process.env.PGHOST || "localhost",
  database: process.env.PGDATABASE || "postgres",
  user: process.env.PGUSER || "postgres",
  password: process.env.PGPASSWORD || "",
  port: Number(process.env.PGPORT) || 5432,
  ssl: { rejectUnauthorized: false },
});

// ✅ Python 스크립트 실행 함수 (진행률 추적 포함)
function runPython(scriptPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const proc = spawn("python3", [scriptPath]);

    proc.stdout.on("data", (data) => {
      const text = data.toString().trim();
      console.log(`📤 ${scriptPath} stdout: ${text}`);

      // 진행률 [n/200] 형식 감지
      const match = text.match(/\[(\d+)\s*\/\s*(\d+)\]/);
      if (match) {
        const current = parseInt(match[1], 10);
        const total = parseInt(match[2], 10);
        if (!isNaN(current) && !isNaN(total)) {
          dataCollectionProgress.current = current;
          dataCollectionProgress.total = total;
        }
      }
    });

    proc.stderr.on("data", (data) => {
      console.error(`⚠️ ${scriptPath} stderr: ${data.toString().trim()}`);
    });

    proc.on("close", (code) => {
      if (code === 0) {
        console.log(`✅ ${scriptPath} 실행 종료`);
        resolve();
      } else {
        reject(new Error(`${scriptPath} failed with code ${code}`));
      }
    });
  });
}

// ✅ Best K Python 스크립트 실행 함수 (JSON 입력/출력 처리)
function runBestKPython(inputData: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const proc = spawn("python3", ["server/services/best-k-calculator.py"], {
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      const text = data.toString().trim();
      stderr += text + "\n";
      console.log(`📤 Best K stderr: ${text}`);

      // Best K 진행률 추적
      const successMatch = text.match(/\[SUCCESS\].*\((\d+)\/(\d+)\)/);
      const infoMatch = text.match(/\[(\d+)\/(\d+)\]/);

      if (successMatch || infoMatch) {
        const match = successMatch || infoMatch;
        const current = parseInt(match[1], 10);
        const total = parseInt(match[2], 10);
        if (!isNaN(current) && !isNaN(total)) {
          bestKProgress.current = current;
          bestKProgress.total = total;
        }
      }
    });

    proc.on("close", (code) => {
      bestKProgress.isRunning = false;

      if (code === 0) {
        try {
          const result = JSON.parse(stdout);
          console.log(`✅ Best K 계산 완료`);
          resolve(result);
        } catch (e) {
          reject(new Error(`JSON 파싱 실패: ${e}`));
        }
      } else {
        reject(new Error(`Best K 계산 실패 (code: ${code})\n${stderr}`));
      }
    });

    proc.on("error", (error) => {
      bestKProgress.isRunning = false;
      reject(new Error(`Python 프로세스 시작 실패: ${error}`));
    });

    // JSON 입력 전송
    proc.stdin.write(JSON.stringify(inputData));
    proc.stdin.end();
  });
}

// ✅ 기간 타입을 날짜로 변환하는 함수
function calculatePeriodDates(
  period: string,
  customStart?: string,
  customEnd?: string,
): { startDate: string; endDate: string } {
  const today = new Date();
  const endDate = today.toISOString().split("T")[0]; // YYYY-MM-DD

  if (period === "custom") {
    if (!customStart || !customEnd) {
      throw new Error("커스텀 기간 선택 시 시작일과 종료일이 필요합니다");
    }
    return { startDate: customStart, endDate: customEnd };
  }

  const periodMap: { [key: string]: number } = {
    days_3: 3,
    week_1: 7,
    month_1: 30,
    month_3: 90,
    quarter: 90,
    half_year: 180,
    year_1: 365,
  };

  const days = periodMap[period];
  if (!days) {
    throw new Error(`지원하지 않는 기간 타입: ${period}`);
  }

  const startDateObj = new Date(today);
  startDateObj.setDate(startDateObj.getDate() - days);
  const startDate = startDateObj.toISOString().split("T")[0];

  return { startDate, endDate };
}

// ================== BEST K 관련 API ==================

// ✅ Best K 계산 (기간 선택 지원)
router.post("/calculate-best-k", async (req, res) => {
  try {
    if (bestKProgress.isRunning) {
      return res.status(400).json({
        success: false,
        message: "Best K 계산이 이미 진행 중입니다",
      });
    }

    const { period, startDate, endDate, market = "ALL" } = req.body;

    if (!period) {
      return res.status(400).json({
        success: false,
        message: "기간을 선택해주세요",
      });
    }

    // 기간 계산
    let calculatedStart: string, calculatedEnd: string;
    try {
      const dates = calculatePeriodDates(period, startDate, endDate);
      calculatedStart = dates.startDate;
      calculatedEnd = dates.endDate;
    } catch (error) {
      return res.status(400).json({
        success: false,
        message: error instanceof Error ? error.message : "날짜 계산 오류",
      });
    }

    console.log(
      `📥 Best K 계산 시작 - 기간: ${calculatedStart} ~ ${calculatedEnd}, 시장: ${market}`,
    );

    // 진행률 초기화
    bestKProgress.current = 0;
    bestKProgress.total = 200;
    bestKProgress.isRunning = true;

    // Python 스크립트 실행
    const inputData = {
      period,
      startDate: calculatedStart,
      endDate: calculatedEnd,
      market: market === "ALL" ? null : market,
    };

    const result = await runBestKPython(inputData);

    return res.status(200).json(result);
  } catch (err) {
    bestKProgress.isRunning = false;
    console.error("❌ Best K 계산 오류:", err);
    return res.status(500).json({
      success: false,
      message: `Best K 계산 실패: ${err instanceof Error ? err.message : "알 수 없는 오류"}`,
    });
  }
});

// ✅ Best K 계산 진행률 확인 API
router.get("/best-k-progress", (_req, res) => {
  const { current, total, isRunning } = bestKProgress;
  res.status(200).json({
    current,
    total,
    percent: total > 0 ? Math.floor((current / total) * 100) : 0,
    isRunning,
  });
});

// ✅ 사용 가능한 기간 옵션 조회
router.get("/best-k-periods", (_req, res) => {
  const periods = [
    {
      value: "days_3",
      label: "최근 3일",
      description: "최근 3일간의 데이터 기준",
    },
    {
      value: "week_1",
      label: "1주일",
      description: "최근 1주일간의 데이터 기준",
    },
    {
      value: "month_1",
      label: "1개월",
      description: "최근 1개월간의 데이터 기준",
    },
    {
      value: "month_3",
      label: "3개월",
      description: "최근 3개월간의 데이터 기준",
    },
    {
      value: "quarter",
      label: "분기",
      description: "최근 분기(3개월)간의 데이터 기준",
    },
    {
      value: "half_year",
      label: "반기",
      description: "최근 반기(6개월)간의 데이터 기준",
    },
    { value: "year_1", label: "1년", description: "최근 1년간의 데이터 기준" },
    {
      value: "custom",
      label: "사용자 지정",
      description: "직접 시작일과 종료일을 선택",
    },
  ];

  const markets = [
    { value: "ALL", label: "전체", description: "KOSPI + KOSDAQ 전체" },
    { value: "KOSPI", label: "KOSPI", description: "KOSPI 시장만" },
    { value: "KOSDAQ", label: "KOSDAQ", description: "KOSDAQ 시장만" },
  ];

  res.json({
    success: true,
    data: {
      periods,
      markets,
    },
  });
});

// ✅ Best K 값 상태 조회
router.get("/best-k-status", async (_req, res) => {
  try {
    const client = await pool.connect();

    // 최신 날짜 조회
    const { rows: dateRows } = await client.query(
      `SELECT MAX(date) AS latest_date FROM daily_market_cap`,
    );
    const latestDate = dateRows[0]?.latest_date;

    if (!latestDate) {
      client.release();
      return res.json({
        success: true,
        data: {
          totalSymbols: 0,
          updatedSymbols: 0,
          nullSymbols: 0,
          lastUpdated: null,
          updateRate: 0,
        },
      });
    }

    // Best K 상태 조회
    const { rows: statusRows } = await client.query(
      `
      SELECT 
        COUNT(*) as total_symbols,
        COUNT(best_k) as updated_symbols,
        COUNT(*) - COUNT(best_k) as null_symbols
      FROM daily_market_cap 
      WHERE date = $1
    `,
      [latestDate],
    );

    const stats = statusRows[0];
    const updateRate =
      stats.total_symbols > 0
        ? Math.round((stats.updated_symbols / stats.total_symbols) * 100)
        : 0;

    client.release();

    res.json({
      success: true,
      data: {
        totalSymbols: parseInt(stats.total_symbols),
        updatedSymbols: parseInt(stats.updated_symbols),
        nullSymbols: parseInt(stats.null_symbols),
        lastUpdated: latestDate,
        updateRate,
      },
    });
  } catch (error) {
    console.error("[ERROR] Best K 상태 조회 오류:", error);
    res.status(500).json({
      success: false,
      message: `서버 오류: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
    });
  }
});

// ================== 기존 API들 ==================

// ✅ 수집 상태 확인 API (단계별 의존성 체크 개선)
router.get("/collection-status", async (_req, res) => {
  try {
    const client = await pool.connect();

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // 시가총액 수집 완료 여부 및 날짜 (조건 완화)
    const { rows: capRows } = await client.query(`
      SELECT MAX(date) AS date, COUNT(*) as count 
      FROM daily_market_cap 
      WHERE market_cap IS NOT NULL AND market_cap > 0
    `);

    const marketCapDate: Date | null = capRows[0]?.date || null;
    const marketCapCount = parseInt(capRows[0]?.count || "0");

    // 조건 완화: 오늘 데이터가 있고 50개 이상이면 완료로 인정
    const marketCapDone =
      marketCapDate &&
      new Date(marketCapDate).toDateString() === today.toDateString() &&
      marketCapCount >= 50; // 100개 → 50개로 완화

    console.log(
      `🔍 시가총액 상태 체크: 날짜=${marketCapDate}, 개수=${marketCapCount}, 완료=${marketCapDone}`,
    );

    // OHLCV 수집 완료 여부 및 날짜
    let ohlcvDone = false;
    let ohlcvDate: Date | null = null;

    if (marketCapDone) {
      const { rows: ohlcvRows } = await client.query(
        `
        SELECT MAX(ds.date) AS date, COUNT(DISTINCT ds.ticker) as ticker_count
        FROM daily_stock_data ds
        INNER JOIN daily_market_cap dm ON ds.ticker = dm.ticker
        WHERE dm.date = $1
        AND ds.date >= $1 - INTERVAL '30 days'
      `,
        [marketCapDate],
      );

      ohlcvDate = ohlcvRows[0]?.date || null;
      const ohlcvTickerCount = parseInt(ohlcvRows[0]?.ticker_count || "0");

      // 조건 완화: 오늘 데이터가 있고 50% 이상 커버하면 완료
      ohlcvDone =
        ohlcvDate &&
        new Date(ohlcvDate).toDateString() === today.toDateString() &&
        ohlcvTickerCount >= Math.max(Math.floor(marketCapCount * 0.5), 25); // 최소 25개

      console.log(
        `🔍 OHLCV 상태 체크: 날짜=${ohlcvDate}, 종목수=${ohlcvTickerCount}, 완료=${ohlcvDone}`,
      );
    }

    // Best K 계산 완료 여부 (조건 완화)
    let bestKDone = false;
    if (ohlcvDone && marketCapDate) {
      const { rows: bestKRows } = await client.query(
        `
        SELECT COUNT(*) as count
        FROM best_k_analysis bka
        INNER JOIN daily_market_cap dm ON bka.ticker = dm.ticker
        WHERE dm.date = $1 
        AND bka.analysis_date = $1
      `,
        [marketCapDate],
      );

      const bestKCount = parseInt(bestKRows[0]?.count || "0");
      bestKDone = bestKCount >= Math.max(Math.floor(marketCapCount * 0.3), 10); // 30% 이상, 최소 10개

      console.log(`🔍 Best K 상태 체크: 개수=${bestKCount}, 완료=${bestKDone}`);
    }

    client.release();

    return res.status(200).json({
      success: true,
      data: {
        marketCapDone,
        ohlcvDone,
        bestKDone,
        marketCapDate,
        ohlcvDate,
        counts: {
          marketCap: marketCapCount,
          ohlcv: ohlcvDate ? marketCapCount : 0,
          bestK: bestKDone ? marketCapCount : 0,
        },
      },
    });
  } catch (err) {
    console.error("❌ 상태 확인 오류:", err);
    return res.status(500).json({ success: false, message: "상태 확인 실패" });
  }
});

// ✅ 시가총액 수집만 실행
router.post("/collect-market-cap", async (_req, res) => {
  console.log("📥 시가총액 수집 시작");
  dataCollectionProgress.current = 0;
  dataCollectionProgress.total = 200;
  try {
    await runPython("server/services/collector_market_cap.py");
    res.status(200).json({ success: true, message: "시가총액 수집 완료" });
  } catch (err) {
    console.error("❌ 시가총액 수집 오류:", err);
    res.status(500).json({ success: false, message: "시가총액 수집 실패" });
  }
});

// ✅ 1Y 수집만 실행
router.post("/collect-ohlcv", async (_req, res) => {
  console.log("📥 1Y 수집 시작");
  dataCollectionProgress.current = 0;
  dataCollectionProgress.total = 200;
  try {
    await runPython("server/services/collector.py");
    res.status(200).json({ success: true, message: "1Y 수집 완료" });
  } catch (err) {
    console.error("❌ 1Y 수집 오류:", err);
    res.status(500).json({ success: false, message: "1Y 수집 실패" });
  }
});

// ✅ 데이터 수집 API
router.post("/collect-data", async (_req, res) => {
  console.log("📥 /api/collect-data 호출됨");

  dataCollectionProgress.current = 0;
  dataCollectionProgress.total = 200;

  try {
    await runPython("server/services/collector_market_cap.py");
    await runPython("server/services/collector.py");

    return res.status(200).json({
      success: true,
      message: "Collector 실행 성공",
      data: [],
    });
  } catch (err) {
    console.error("❌ Collector 실행 중 에러:", err);
    return res.status(500).json({
      success: false,
      message: "Collector 실행 실패",
      error: String(err),
    });
  }
});

// ✅ 수집 진행률 확인 API
router.get("/collect-progress", (_req, res) => {
  const { current, total } = dataCollectionProgress;
  res.status(200).json({
    current,
    total,
    percent: total > 0 ? Math.floor((current / total) * 100) : 0,
  });
});

// ✅ 최신 시가총액 데이터 조회 API
router.get("/market-latest", async (_req, res) => {
  try {
    const client = await pool.connect();

    const {
      rows: [latestDateRow],
    } = await client.query(`SELECT MAX(date) as latest FROM daily_market_cap`);

    const latestDate = latestDateRow?.latest;
    if (!latestDate) {
      return res.status(404).json({ success: false, message: "데이터 없음" });
    }

    const { rows } = await client.query(
      `SELECT * FROM daily_market_cap WHERE date = $1 ORDER BY market_cap DESC`,
      [latestDate],
    );

    client.release();

    return res.status(200).json({
      success: true,
      message: "최신 시가총액 데이터",
      data: rows,
    });
  } catch (err) {
    console.error("❌ market-latest API 에러:", err);
    return res.status(500).json({
      success: false,
      message: "데이터 조회 실패",
      error: String(err),
    });
  }
});

export default router;
