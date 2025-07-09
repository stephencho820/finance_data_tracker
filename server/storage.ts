import { stockData, dailyStockData, type StockData, type InsertStockData, type DailyStockData, type InsertDailyStockData } from "@shared/schema";
import { db } from "./db";
import { eq, desc, and } from "drizzle-orm";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  getStockData(id: number): Promise<StockData | undefined>;
  getStockDataBySymbol(symbol: string): Promise<StockData[]>;
  createStockData(data: InsertStockData): Promise<StockData>;
  getAllStockData(): Promise<StockData[]>;
  createManyStockData(data: InsertStockData[]): Promise<StockData[]>;
  
  // Daily Stock Data methods
  getDailyStockData(id: number): Promise<DailyStockData | undefined>;
  getDailyStockDataBySymbol(symbol: string): Promise<DailyStockData[]>;
  getDailyStockDataByDate(date: string): Promise<DailyStockData[]>;
  getDailyStockDataByMarketAndRank(market: string, rankType: string, date: string): Promise<DailyStockData[]>;
  createDailyStockData(data: InsertDailyStockData): Promise<DailyStockData>;
  getAllDailyStockData(): Promise<DailyStockData[]>;
  createManyDailyStockData(data: InsertDailyStockData[]): Promise<DailyStockData[]>;
}

export class DatabaseStorage implements IStorage {
  async getStockData(id: number): Promise<StockData | undefined> {
    const [data] = await db.select().from(stockData).where(eq(stockData.id, id));
    return data || undefined;
  }

  async getStockDataBySymbol(symbol: string): Promise<StockData[]> {
    const data = await db.select().from(stockData).where(eq(stockData.symbol, symbol));
    return data;
  }

  async createStockData(insertData: InsertStockData): Promise<StockData> {
    const [data] = await db
      .insert(stockData)
      .values(insertData)
      .returning();
    return data;
  }

  async createManyStockData(insertData: InsertStockData[]): Promise<StockData[]> {
    if (!insertData || insertData.length === 0) {
      return [];
    }
    const data = await db
      .insert(stockData)
      .values(insertData)
      .returning();
    return data;
  }

  async getAllStockData(): Promise<StockData[]> {
    const data = await db.select().from(stockData).orderBy(desc(stockData.createdAt));
    return data;
  }

  // Daily Stock Data methods
  async getDailyStockData(id: number): Promise<DailyStockData | undefined> {
    const [result] = await db.select().from(dailyStockData).where(eq(dailyStockData.id, id));
    return result || undefined;
  }

  async getDailyStockDataBySymbol(symbol: string): Promise<DailyStockData[]> {
    const result = await db.select().from(dailyStockData).where(eq(dailyStockData.symbol, symbol)).orderBy(desc(dailyStockData.date));
    return result;
  }

  async getDailyStockDataByDate(date: string): Promise<DailyStockData[]> {
    const result = await db.select().from(dailyStockData).where(eq(dailyStockData.date, date));
    return result;
  }

  async getDailyStockDataByMarketAndRank(market: string, rankType: string, date: string): Promise<DailyStockData[]> {
    const result = await db.select().from(dailyStockData)
      .where(
        and(
          eq(dailyStockData.market, market),
          eq(dailyStockData.rank_type, rankType),
          eq(dailyStockData.date, date)
        )
      )
      .orderBy(dailyStockData.rank);
    return result;
  }

  async createDailyStockData(insertData: InsertDailyStockData): Promise<DailyStockData> {
    const [result] = await db.insert(dailyStockData).values(insertData).returning();
    return result;
  }

  async getAllDailyStockData(): Promise<DailyStockData[]> {
    const result = await db.select().from(dailyStockData).orderBy(desc(dailyStockData.date));
    return result;
  }

  async createManyDailyStockData(insertData: InsertDailyStockData[]): Promise<DailyStockData[]> {
    const result = await db.insert(dailyStockData).values(insertData).returning();
    return result;
  }
}

export const storage = new DatabaseStorage();
