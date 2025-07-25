// ✅ 수집 상태 확인 API
router.get("/collection-status", async (_req, res) => {
  try {
    const client = await pool.connect();

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // ✅ 시가총액 수집 완료 여부
    const { rows: capRows } = await client.query(`
      SELECT MAX(date) AS date FROM daily_market_cap WHERE market_cap IS NOT NULL
    `);
    const marketCapDate: Date | null = capRows[0]?.date || null;
    const marketCapDone =
      marketCapDate &&
      new Date(marketCapDate).toDateString() === today.toDateString();

    // ✅ OHLCV 수집 완료 여부
    const { rows: ohlcvRows } = await client.query(`
      SELECT MAX(date) AS date FROM daily_stock_data
    `);
    const ohlcvDate: Date | null = ohlcvRows[0]?.date || null;
    const ohlcvDone =
      ohlcvDate && new Date(ohlcvDate).toDateString() === today.toDateString();

    // ✅ Best K 계산 완료 여부
    let bestKDone = false;
    if (marketCapDone) {
      const { rows: bestKRows } = await client.query(
        `
        SELECT COUNT(*) FROM daily_market_cap
        WHERE best_k IS NULL AND date = $1
      `,
        [marketCapDate],
      );
      bestKDone = parseInt(bestKRows[0]?.count || "0") === 0;
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
      },
    });
  } catch (err) {
    console.error("❌ 상태 확인 오류:", err);
    return res.status(500).json({ success: false, message: "상태 확인 실패" });
  }
});
