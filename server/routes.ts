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
      const pythonScript = path.join(__dirname, "services", "data-collector-simple.py");
      const pythonProcess = spawn("python3", [pythonScript]);
      
      // Set up timeout (30 seconds)
      const timeout = setTimeout(() => {
        pythonProcess.kill();
        res.status(408).json({
          success: false,
          message: "Data collection timed out",
          error: "The request took too long to process"
        });
      }, 30000);
      
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
      
      pythonProcess.on("close", (code) => {
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
      // Mock stats for now - in a real app, this would query the database
      const stats = {
        totalStocks: 1234,
        averageReturn: 2.34,
        totalVolume: 456700000,
        marketCap: "2,456조원"
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

  const httpServer = createServer(app);
  return httpServer;
}
