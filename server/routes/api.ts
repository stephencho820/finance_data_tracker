// ✅ server/routes/api.ts

import { Router } from "express";
import { exec } from "child_process";
import { promisify } from "util";

const router = Router();
const execAsync = promisify(exec);

router.post("/collect-data", async (req, res) => {
  try {
    console.log("📥 수집 요청 수신됨");
    await execAsync("python3 server/services/collector_market_cap.py");
    await execAsync("python3 server/services/collector.py");

    const db = req.app.get("db");
    const result = await db.query(`
      SELECT *
      FROM daily_market_cap
      WHERE date = (SELECT MAX(date) FROM daily_market_cap)
      ORDER BY market_cap::numeric DESC
    `);

    return res.status(200).json({
      success: true,
      message: "데이터 수집 완료",
      data: result.rows,
    });
  } catch (e) {
    console.error("❌ 수집 실패:", e);
    return res.status(500).json({
      success: false,
      message: "Collector 실행 실패",
      error: String(e),
    });
  }
});

export default router;
