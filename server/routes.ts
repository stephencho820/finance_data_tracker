import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { dataCollectionRequest, stockDataResponse, quickStatsResponse } from "@shared/schema";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export async function registerRoutes(app: Express): Promise<Server> {
  
  // Collect stock data
  app.post("/api/collect-data", async (req, res) => {
    try {
      const validatedRequest = dataCollectionRequest.parse(req.body);
      
      // Spawn Python process for data collection
      const pythonScript = path.join(__dirname, "services", "data-collector-fast.py");
      const pythonProcess = spawn("python3", [pythonScript]);
      
      // Set up timeout (5 minutes for real API data collection)
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        res.status(408).json({
          success: false,
          message: "Data collection timed out",
          error: "The request took too long to process"
        });
      }, 300000);
      
      // Send input data to Python process
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
      
      pythonProcess.on("close", async (code) => {
        clearTimeout(timeout);
        
        if (code !== 0) {
          return res.status(500).json({
            success: false,
            message: "Failed to collect data",
            error: error || "Unknown error occurred"
          });
        }
        
        try {
          const result = JSON.parse(output);
          
          if (!result.success) {
            return res.status(400).json({
              success: false,
              message: result.message,
              error: result.traceback
            });
          }
          
          // Validate response data
          const validatedData = result.data.map((item: any) => 
            stockDataResponse.parse(item)
          );
          
          // Store collected data in database
          const stockDataToInsert = validatedData.map((item: any) => ({
            symbol: item.symbol,
            name: item.name,
            current_price: item.current_price?.toString() || null,
            change: item.change?.toString() || null,
            change_percent: item.change_percent?.toString() || null,
            volume: item.volume || null,
            market_cap: item.market_cap?.toString() || null,
            pe_ratio: item.pe_ratio?.toString() || null,
            pbr: item.pbr?.toString() || null,
            dividend_yield: item.dividend_yield?.toString() || null,
            week_52_high: item.week_52_high?.toString() || null,
            week_52_low: item.week_52_low?.toString() || null,
            sector: item.sector || null,
            industry: item.industry || null,
            beta: item.beta?.toString() || null,
            eps: item.eps?.toString() || null,
            shares_outstanding: item.shares_outstanding?.toString() || null,
            book_value: item.book_value?.toString() || null,
            revenue: item.revenue?.toString() || null,
            net_income: item.net_income?.toString() || null,
            debt_to_equity: item.debt_to_equity?.toString() || null,
            roe: item.roe?.toString() || null,
            roa: item.roa?.toString() || null,
            operating_margin: item.operating_margin?.toString() || null,
            profit_margin: item.profit_margin?.toString() || null,
            revenue_growth: item.revenue_growth?.toString() || null,
            earnings_growth: item.earnings_growth?.toString() || null,
            current_ratio: item.current_ratio?.toString() || null,
            quick_ratio: item.quick_ratio?.toString() || null,
            price_to_sales: item.price_to_sales?.toString() || null,
            price_to_cash_flow: item.price_to_cash_flow?.toString() || null,
            enterprise_value: item.enterprise_value?.toString() || null,
            ev_to_revenue: item.ev_to_revenue?.toString() || null,
            ev_to_ebitda: item.ev_to_ebitda?.toString() || null,
            free_cash_flow: item.free_cash_flow?.toString() || null,
            country: item.country,
            market: item.market,
            date: new Date(item.date),
          }));
          
          try {
            await storage.createManyStockData(stockDataToInsert);
          } catch (dbError) {
            console.error("Failed to store data in database:", dbError);
            // Continue with response even if database storage fails
          }
          
          res.json({
            success: true,
            data: validatedData,
            message: result.message
          });
          
        } catch (parseError) {
          res.status(500).json({
            success: false,
            message: "Failed to parse response data",
            error: parseError instanceof Error ? parseError.message : "Unknown parsing error"
          });
        }
      });
      
    } catch (error) {
      res.status(400).json({
        success: false,
        message: "Invalid request data",
        error: error instanceof Error ? error.message : "Unknown validation error"
      });
    }
  });
  
  // Get quick stats
  app.get("/api/quick-stats", async (req, res) => {
    try {
      const allData = await storage.getAllStockData();
      
      const totalStocks = allData.length;
      const averageReturn = allData.length > 0 
        ? allData.reduce((sum, item) => sum + (parseFloat(item.change_percent || "0")), 0) / allData.length
        : 0;
      const totalVolume = allData.reduce((sum, item) => sum + (item.volume || 0), 0);
      
      const stats = {
        totalStocks,
        averageReturn: Math.round(averageReturn * 100) / 100,
        totalVolume,
        marketCap: totalStocks > 0 ? `${Math.round(totalStocks * 1.2)}조원` : "0조원"
      };
      
      const validatedStats = quickStatsResponse.parse(stats);
      res.json(validatedStats);
      
    } catch (error) {
      res.status(500).json({
        success: false,
        message: "Failed to get quick stats",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  // Get all stored stock data
  app.get("/api/stock-data", async (req, res) => {
    try {
      const allData = await storage.getAllStockData();
      
      const responseData = allData.map(item => ({
        symbol: item.symbol,
        name: item.name,
        current_price: item.current_price ? parseFloat(item.current_price) : null,
        change: item.change ? parseFloat(item.change) : null,
        change_percent: item.change_percent ? parseFloat(item.change_percent) : null,
        volume: item.volume,
        market_cap: item.market_cap,
        pe_ratio: item.pe_ratio ? parseFloat(item.pe_ratio) : null,
        pbr: item.pbr ? parseFloat(item.pbr) : null,
        dividend_yield: item.dividend_yield ? parseFloat(item.dividend_yield) : null,
        week_52_high: item.week_52_high ? parseFloat(item.week_52_high) : null,
        week_52_low: item.week_52_low ? parseFloat(item.week_52_low) : null,
        sector: item.sector,
        industry: item.industry,
        beta: item.beta ? parseFloat(item.beta) : null,
        eps: item.eps ? parseFloat(item.eps) : null,
        shares_outstanding: item.shares_outstanding ? parseFloat(item.shares_outstanding) : null,
        book_value: item.book_value ? parseFloat(item.book_value) : null,
        revenue: item.revenue ? parseFloat(item.revenue) : null,
        net_income: item.net_income ? parseFloat(item.net_income) : null,
        debt_to_equity: item.debt_to_equity ? parseFloat(item.debt_to_equity) : null,
        roe: item.roe ? parseFloat(item.roe) : null,
        roa: item.roa ? parseFloat(item.roa) : null,
        operating_margin: item.operating_margin ? parseFloat(item.operating_margin) : null,
        profit_margin: item.profit_margin ? parseFloat(item.profit_margin) : null,
        revenue_growth: item.revenue_growth ? parseFloat(item.revenue_growth) : null,
        earnings_growth: item.earnings_growth ? parseFloat(item.earnings_growth) : null,
        current_ratio: item.current_ratio ? parseFloat(item.current_ratio) : null,
        quick_ratio: item.quick_ratio ? parseFloat(item.quick_ratio) : null,
        price_to_sales: item.price_to_sales ? parseFloat(item.price_to_sales) : null,
        price_to_cash_flow: item.price_to_cash_flow ? parseFloat(item.price_to_cash_flow) : null,
        enterprise_value: item.enterprise_value ? parseFloat(item.enterprise_value) : null,
        ev_to_revenue: item.ev_to_revenue ? parseFloat(item.ev_to_revenue) : null,
        ev_to_ebitda: item.ev_to_ebitda ? parseFloat(item.ev_to_ebitda) : null,
        free_cash_flow: item.free_cash_flow ? parseFloat(item.free_cash_flow) : null,
        country: item.country,
        market: item.market,
        date: item.date.toISOString().split('T')[0]
      }));
      
      res.json({
        success: true,
        data: responseData,
        total: allData.length
      });
      
    } catch (error) {
      res.status(500).json({
        success: false,
        message: "Failed to get stock data",
        error: error instanceof Error ? error.message : "Unknown error"
      });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
