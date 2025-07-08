import { stockData, type StockData, type InsertStockData } from "@shared/schema";
import { db } from "./db";
import { eq, desc } from "drizzle-orm";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  getStockData(id: number): Promise<StockData | undefined>;
  getStockDataBySymbol(symbol: string): Promise<StockData[]>;
  createStockData(data: InsertStockData): Promise<StockData>;
  getAllStockData(): Promise<StockData[]>;
  createManyStockData(data: InsertStockData[]): Promise<StockData[]>;
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
}

export const storage = new DatabaseStorage();
