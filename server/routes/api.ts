// server/routes/api.ts
import { Router } from "express";
import { exec } from "child_process";
import { promisify } from "util";

const router = Router();
const execAsync = promisify(exec);

router.post("/collect-data", async (req, res) => {
  const { startDate, endDate, market } = req.body;

  if (!startDate || !endDate || !market) {
    return res.status(400).json({
      success: false,
      message: "Invalid request: startDate, endDate, market are required",
    });
  }

  try {
    await execAsync("python3 server/services/collector_market_cap.py");
    await execAsync("python3 server/services/collector.py");

    const marketRes = await fetch(`http://localhost:5000/api/market-latest`);
    const data = await marketRes.json();

    return res.status(200).json({
      success: true,
      message: "데이터 수집 완료",
      data: data.data,
    });
  } catch (err) {
    console.error("데이터 수집 실패:", err);
    return res.status(500).json({
      success: false,
      message: "Collector 실행 실패",
      error: String(err),
    });
  }
});

export default router;
