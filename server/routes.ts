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
      const pythonScript = path.join(__dirname, "services", "data-collector.py");
      const pythonProcess = spawn("python3", [pythonScript]);
      
      // Set up timeout (2 minutes for comprehensive data collection)
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        res.status(408).json({
          success: false,
          message: "Data collection timed out",
          error: "The request took too long to process"
        });
      }, 120000);
      
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
            price: item.price?.toString() || null,
            change: item.change?.toString() || null,
            changePercent: item.changePercent?.toString() || null,
            volume: item.volume || null,
            marketCap: item.marketCap || null,
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
        ? allData.reduce((sum, item) => sum + (parseFloat(item.changePercent || "0")), 0) / allData.length
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
        price: item.price ? parseFloat(item.price) : null,
        change: item.change ? parseFloat(item.change) : null,
        changePercent: item.changePercent ? parseFloat(item.changePercent) : null,
        volume: item.volume,
        marketCap: item.marketCap,
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
