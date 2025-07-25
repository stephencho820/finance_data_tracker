// 📄 server/routes/api.ts
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

// ✅ 수집 상태 확인 API (최종 단계 및 날짜 확인용)
router.get("/collection-status", async (_req, res) => {
  try {
    const client = await pool.connect();

    // 📅 market_cap 기준 최신 날짜
    const { rows: capRows } = await client.query(`
      SELECT MAX(date) AS date
      FROM daily_market_cap
      WHERE market_cap IS NOT NULL
    `);
    const marketCapDate = capRows[0]?.date;

    // 📅 OHLCV 기준 최신 날짜 (모든 OHLCV 필드가 null이 아닌 경우)
    const { rows: ohlcvRows } = await client.query(`
      SELECT MAX(date) AS date
      FROM daily_market_cap
      WHERE open_price IS NOT NULL
        AND high_price IS NOT NULL
        AND low_price IS NOT NULL
        AND close_price IS NOT NULL
        AND volume IS NOT NULL
    `);
    const ohlcvDate = ohlcvRows[0]?.date;

    // 🧠 최종 단계 판단
    let step = 0;
    if (marketCapDate) step = 1;
    if (ohlcvDate && ohlcvDate.toISOString() === marketCapDate?.toISOString())
      step = 2;

    const { rows: bestKRows } = await client.query(
      `
      SELECT COUNT(*) FROM daily_market_cap
      WHERE best_k IS NOT NULL AND date = $1
    `,
      [ohlcvDate],
    );

    const bestKCount = parseInt(bestKRows[0]?.count || "0");
    if (step === 2 && bestKCount > 0) step = 3;

    client.release();

    return res.status(200).json({
      success: true,
      step,
      marketCapDate,
      ohlcvDate,
    });
  } catch (err) {
    console.error("❌ 상태 확인 오류:", err);
    return res.status(500).json({ success: false, message: "상태 확인 실패" });
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
