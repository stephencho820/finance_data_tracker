import type { NextApiRequest, NextApiResponse } from "next";
import { db } from "@/lib/db"; // DB 연결 유틸

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  try {
    const result = await db.query(`
      SELECT *
      FROM daily_market_cap
      WHERE date = (SELECT MAX(date) FROM daily_market_cap)
      ORDER BY market_cap::numeric DESC
    `);

    return res.status(200).json({
      success: true,
      data: result.rows,
    });
  } catch (err) {
    console.error("📛 DB 조회 실패:", err instanceof Error ? err.message : err);
    return res.status(500).json({
      success: false,
      message: "DB 조회 중 오류가 발생했습니다.",
    });
  }
}
