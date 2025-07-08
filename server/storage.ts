import { type StockData, type InsertStockData } from "@shared/schema";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  getStockData(id: number): Promise<StockData | undefined>;
  getStockDataBySymbol(symbol: string): Promise<StockData[]>;
  createStockData(data: InsertStockData): Promise<StockData>;
  getAllStockData(): Promise<StockData[]>;
}

export class MemStorage implements IStorage {
  private stockData: Map<number, StockData>;
  currentId: number;

  constructor() {
    this.stockData = new Map();
    this.currentId = 1;
  }

  async getStockData(id: number): Promise<StockData | undefined> {
    return this.stockData.get(id);
  }

  async getStockDataBySymbol(symbol: string): Promise<StockData[]> {
    return Array.from(this.stockData.values()).filter(
      (data) => data.symbol === symbol,
    );
  }

  async createStockData(insertData: InsertStockData): Promise<StockData> {
    const id = this.currentId++;
    const data: StockData = { 
      ...insertData, 
      id,
      createdAt: new Date(),
      price: insertData.price ?? null,
      change: insertData.change ?? null,
      changePercent: insertData.changePercent ?? null,
      volume: insertData.volume ?? null,
      marketCap: insertData.marketCap ?? null,
    };
    this.stockData.set(id, data);
    return data;
  }

  async getAllStockData(): Promise<StockData[]> {
    return Array.from(this.stockData.values());
  }
}

export const storage = new MemStorage();
