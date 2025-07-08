import { pgTable, text, serial, timestamp, decimal, integer } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const stockData = pgTable("stock_data", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  name: text("name").notNull(),
  price: decimal("price", { precision: 10, scale: 2 }),
  change: decimal("change", { precision: 10, scale: 2 }),
  changePercent: decimal("change_percent", { precision: 5, scale: 2 }),
  volume: integer("volume"),
  marketCap: text("market_cap"),
  peRatio: decimal("pe_ratio", { precision: 8, scale: 2 }),
  pbr: decimal("pbr", { precision: 8, scale: 2 }),
  dividendYield: text("dividend_yield"),
  week52High: decimal("week_52_high", { precision: 10, scale: 2 }),
  week52Low: decimal("week_52_low", { precision: 10, scale: 2 }),
  sector: text("sector"),
  industry: text("industry"),
  beta: decimal("beta", { precision: 5, scale: 2 }),
  eps: decimal("eps", { precision: 10, scale: 2 }),
  sharesOutstanding: text("shares_outstanding"),
  tradingValue: text("trading_value"),
  openPrice: decimal("open_price", { precision: 10, scale: 2 }),
  highPrice: decimal("high_price", { precision: 10, scale: 2 }),
  lowPrice: decimal("low_price", { precision: 10, scale: 2 }),
  country: text("country").notNull(),
  market: text("market").notNull(),
  date: timestamp("date").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const dataCollectionRequest = z.object({
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  endDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  country: z.enum(["korea", "usa"]),
  market: z.string(),
  sortBy: z.enum(['market_cap', 'pe_ratio', 'pbr', 'dividend_yield', 'volume', 'current_price']).optional(),
  limit: z.number().min(1).max(100).optional(),
});

export const stockDataResponse = z.object({
  symbol: z.string(),
  name: z.string(),
  price: z.number().nullable(),
  change: z.number().nullable(),
  changePercent: z.number().nullable(),
  volume: z.number().nullable(),
  marketCap: z.string().nullable(),
  peRatio: z.union([z.number(), z.string()]).nullable().optional(),
  pbr: z.union([z.number(), z.string()]).nullable().optional(),
  dividendYield: z.string().nullable().optional(),
  week52High: z.number().nullable().optional(),
  week52Low: z.number().nullable().optional(),
  sector: z.string().nullable().optional(),
  industry: z.string().nullable().optional(),
  beta: z.number().nullable().optional(),
  eps: z.number().nullable().optional(),
  sharesOutstanding: z.string().nullable().optional(),
  tradingValue: z.string().nullable().optional(),
  openPrice: z.number().nullable().optional(),
  highPrice: z.number().nullable().optional(),
  lowPrice: z.number().nullable().optional(),
  country: z.string(),
  market: z.string(),
  date: z.string(),
});

export const quickStatsResponse = z.object({
  totalStocks: z.number(),
  averageReturn: z.number(),
  totalVolume: z.number(),
  marketCap: z.string(),
});

export type DataCollectionRequest = z.infer<typeof dataCollectionRequest>;
export type StockDataResponse = z.infer<typeof stockDataResponse>;
export type QuickStatsResponse = z.infer<typeof quickStatsResponse>;
export type StockData = typeof stockData.$inferSelect;
export type InsertStockData = typeof stockData.$inferInsert;
