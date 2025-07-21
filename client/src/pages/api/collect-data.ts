import type { NextApiRequest, NextApiResponse } from "next";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  if (req.method !== "POST") {
    return res
      .status(405)
      .json({ success: false, message: "Method Not Allowed" });
  }

  try {
    console.log("📦 collector_market_cap.py 실행 시작");
    const result1 = await execAsync(
      "python3 server/services/collector_market_cap.py",
    );
    console.log("✅ collector_market_cap.py stdout:", result1.stdout);
    console.error("⚠️ stderr:", result1.stderr);

    console.log("📦 collector.py 실행 시작");
    const result2 = await execAsync("python3 server/services/collector.py");
    console.log("✅ collector.py stdout:", result2.stdout);
    console.error("⚠️ stderr:", result2.stderr);

    const host = req.headers.host ?? "localhost:3000";
    const marketRes = await fetch(`http://${host}/api/market-latest`);
    const data = await marketRes.json();

    if (!marketRes.ok) {
      throw new Error("market-latest API 호출 실패");
    }

    return res.status(200).json({
      success: true,
      message: "데이터 수집 완료",
      data: data.data,
    });
  } catch (error) {
    console.error("❌ 수집 실패:", error);
    return res.status(500).json({
      success: false,
      message: "Collector 실행 실패",
      error: String(error),
    });
  }
}
