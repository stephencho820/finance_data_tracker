import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import {
  dataCollectionRequest,
  stockDataResponse,
  quickStatsResponse,
} from "@shared/schema";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { DataCollectionScheduler } from "./services/scheduler";
import apiRouter from "./routes/api"; // ✅ 추가됨

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export async function registerRoutes(app: Express): Promise<Server> {
  // 🔹 Best K Calculation
  app.post("/api/calculate-best-k", async (req, res) => {
    try {
      const validatedRequest = dataCollectionRequest.parse(req.body);
      const pythonScript = path.join(
        __dirname,
        "services",
        "best-k-calculator.py",
      );
      const pythonProcess = spawn("python3", [pythonScript]);

      const timeout = setTimeout(() => {
        pythonProcess.kill();
        res.status(408).json({
          success: false,
          message: "Best k calculation timed out",
        });
      }, 600000);

      pythonProcess.stdin.write(JSON.stringify(validatedRequest));
      pythonProcess.stdin.end();

      let output = "";
      let error = "";

      pythonProcess.stdout.on("data", (data) => {
        output += data.toString();
      });

      pythonProcess.stderr.on("data", (data) => {
        error += data.toString();
      });

      pythonProcess.on("close", () => {
        clearTimeout(timeout);
        if (error) {
          return res
            .status(500)
            .json({ success: false, message: "Execution error", error });
        }
        try {
          const result = JSON.parse(output);
          if (!result.success) {
            return res
              .status(400)
              .json({ success: false, message: result.message });
          }
          res.json({
            success: true,
            data: result.data,
            message: result.message,
          });
        } catch (e) {
          res.status(500).json({
            success: false,
            message: "JSON parse failed",
            error: e instanceof Error ? e.message : "unknown",
          });
        }
      });
    } catch (e) {
      res.status(400).json({
        success: false,
        message: "Invalid request",
        error: e instanceof Error ? e.message : "unknown",
      });
    }
  });

  // 🔹 수동 일일 수집
  app.post("/api/collect-daily-data", async (req, res) => {
    try {
      const { market } = req.body;
      if (!market || !["KOSPI", "KOSDAQ"].includes(market)) {
        return res
          .status(400)
          .json({ success: false, message: "Invalid market" });
      }

      const scheduler = DataCollectionScheduler.getInstance();
      const result = await scheduler.manualCollect(market);

      res.json({
        success: true,
        data: result,
        message: `Daily data collection completed for ${market}`,
      });
    } catch (e) {
      res.status(500).json({
        success: false,
        message: "Failed to collect daily data",
        error: e instanceof Error ? e.message : "Unknown error",
      });
    }
  });

  // 🔹 퀵 통계
  app.get("/api/quick-stats", async (_req, res) => {
    try {
      const allData = await storage.getAllStockData();

      const totalStocks = allData.length;
      const averageReturn =
        allData.reduce(
          (sum, d) => sum + (parseFloat(d.change_percent || "0") || 0),
          0,
        ) / (totalStocks || 1);
      const totalVolume = allData.reduce((sum, d) => sum + (d.volume || 0), 0);

      const stats = quickStatsResponse.parse({
        totalStocks,
        averageReturn: Math.round(averageReturn * 100) / 100,
        totalVolume,
        marketCap:
          totalStocks > 0 ? `${Math.round(totalStocks * 1.2)}조원` : "0조원",
      });

      res.json(stats);
    } catch (e) {
      res.status(500).json({
        success: false,
        message: "Failed to get stats",
        error: e instanceof Error ? e.message : "unknown",
      });
    }
  });

  // 🔹 저장된 주식 데이터 조회
  app.get("/api/stock-data", async (_req, res) => {
    try {
      const allData = await storage.getAllStockData();

      const responseData = allData.map((item) => ({
        symbol: item.symbol,
        name: item.name,
        current_price: parseFloat(item.current_price ?? "0") || null,
        change: parseFloat(item.change ?? "0") || null,
        change_percent: parseFloat(item.change_percent ?? "0") || null,
        volume: item.volume,
        market_cap: item.market_cap,
        pe_ratio: parseFloat(item.pe_ratio ?? "0") || null,
        pbr: parseFloat(item.pbr ?? "0") || null,
        dividend_yield: parseFloat(item.dividend_yield ?? "0") || null,
        week_52_high: parseFloat(item.week_52_high ?? "0") || null,
        week_52_low: parseFloat(item.week_52_low ?? "0") || null,
        country: item.country,
        market: item.market,
        date: item.date.toISOString().split("T")[0],
      }));

      res.json({ success: true, data: responseData, total: allData.length });
    } catch (e) {
      res.status(500).json({
        success: false,
        message: "Failed to get stock data",
        error: e instanceof Error ? e.message : "Unknown error",
      });
    }
  });

  // 🔹 일별 데이터 (daily_market_cap 테이블 기반)
  app.get("/api/daily-stock-data", async (req, res) => {
    try {
      const { date, market, rank_type } = req.query;

      if (date && market && rank_type) {
        const result = await storage.getDailyStockDataByMarketAndRank(
          market as string,
          rank_type as string,
          date as string,
        );
        return res.json(result);
      }

      if (date) {
        const result = await storage.getDailyStockDataByDate(date as string);
        return res.json(result);
      }

      const result = await storage.getAllDailyStockData();
      res.json(result);
    } catch (e) {
      console.error("Error getting daily stock data:", e);
      res.status(500).json({ error: "Failed to get daily stock data" });
    }
  });

  // ✅ /api 라우터 통합 등록
  app.use("/api", apiRouter);

  // 서버 생성
  const httpServer = createServer(app);
  return httpServer;
}
