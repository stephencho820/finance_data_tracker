import { pgTable, text, serial, timestamp, decimal, integer, date, real } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const stockData = pgTable("stock_data", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  name: text("name").notNull(),
  current_price: decimal("current_price", { precision: 10, scale: 2 }),
  change: decimal("change", { precision: 10, scale: 2 }),
  change_percent: decimal("change_percent", { precision: 5, scale: 2 }),
  volume: integer("volume"),
  market_cap: text("market_cap"),
  pe_ratio: decimal("pe_ratio", { precision: 8, scale: 2 }),
  pbr: decimal("pbr", { precision: 8, scale: 2 }),
  dividend_yield: text("dividend_yield"),
  week_52_high: decimal("week_52_high", { precision: 10, scale: 2 }),
  week_52_low: decimal("week_52_low", { precision: 10, scale: 2 }),
  sector: text("sector"),
  industry: text("industry"),
  beta: decimal("beta", { precision: 5, scale: 2 }),
  eps: decimal("eps", { precision: 10, scale: 2 }),
  shares_outstanding: text("shares_outstanding"),
  book_value: decimal("book_value", { precision: 10, scale: 2 }),
  revenue: text("revenue"),
  net_income: text("net_income"),
  debt_to_equity: decimal("debt_to_equity", { precision: 5, scale: 2 }),
  roe: decimal("roe", { precision: 5, scale: 2 }),
  roa: decimal("roa", { precision: 5, scale: 2 }),
  operating_margin: decimal("operating_margin", { precision: 5, scale: 2 }),
  profit_margin: decimal("profit_margin", { precision: 5, scale: 2 }),
  revenue_growth: decimal("revenue_growth", { precision: 5, scale: 2 }),
  earnings_growth: decimal("earnings_growth", { precision: 5, scale: 2 }),
  current_ratio: decimal("current_ratio", { precision: 5, scale: 2 }),
  quick_ratio: decimal("quick_ratio", { precision: 5, scale: 2 }),
  price_to_sales: decimal("price_to_sales", { precision: 5, scale: 2 }),
  price_to_cash_flow: decimal("price_to_cash_flow", { precision: 5, scale: 2 }),
  enterprise_value: text("enterprise_value"),
  ev_to_revenue: decimal("ev_to_revenue", { precision: 5, scale: 2 }),
  ev_to_ebitda: decimal("ev_to_ebitda", { precision: 5, scale: 2 }),
  free_cash_flow: text("free_cash_flow"),
  country: text("country").notNull(),
  market: text("market").notNull(),
  date: timestamp("date").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

// 5년치 일일 데이터 저장 테이블
export const dailyStockData = pgTable("daily_stock_data", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  name: text("name").notNull(),
  date: date("date").notNull(),
  open_price: decimal("open_price", { precision: 10, scale: 2 }),
  high_price: decimal("high_price", { precision: 10, scale: 2 }),
  low_price: decimal("low_price", { precision: 10, scale: 2 }),
  close_price: decimal("close_price", { precision: 10, scale: 2 }),
  volume: integer("volume"),
  market_cap: text("market_cap"),
  market: text("market").notNull(), // KOSPI, KOSDAQ
  rank_by_market_cap: integer("rank_by_market_cap"),
  rank_by_volume: integer("rank_by_volume"),
  best_k_value: decimal("best_k_value", { precision: 10, scale: 4 }), // 알고리즘 계산 결과
  createdAt: timestamp("created_at").defaultNow(),
});

// 데이터 수집 작업 로그 테이블
export const dataCollectionLog = pgTable("data_collection_log", {
  id: serial("id").primaryKey(),
  collection_date: date("collection_date").notNull(),
  market: text("market").notNull(),
  total_stocks: integer("total_stocks"),
  status: text("status").notNull(), // success, failed, in_progress
  error_message: text("error_message"),
  execution_time: integer("execution_time"), // milliseconds
  createdAt: timestamp("created_at").defaultNow(),
});

export const dataCollectionRequest = z.object({
  startDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  endDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  country: z.enum(["korea", "usa"]),
  market: z.string(),
  sortBy: z.enum(['market_cap', 'volume']).optional(),
  limit: z.number().min(1).max(500).optional(),
});

export const stockDataResponse = z.object({
  symbol: z.string(),
  name: z.string(),
  current_price: z.number().nullable(),
  change: z.number().nullable(),
  change_percent: z.number().nullable(),
  volume: z.number().nullable(),
  market_cap: z.number().nullable(),
  pe_ratio: z.union([z.number(), z.string()]).nullable().optional(),
  pbr: z.union([z.number(), z.string()]).nullable().optional(),
  dividend_yield: z.union([z.number(), z.string()]).nullable().optional(),
  week_52_high: z.number().nullable().optional(),
  week_52_low: z.number().nullable().optional(),
  sector: z.string().nullable().optional(),
  industry: z.string().nullable().optional(),
  beta: z.number().nullable().optional(),
  eps: z.number().nullable().optional(),
  shares_outstanding: z.number().nullable().optional(),
  book_value: z.number().nullable().optional(),
  revenue: z.number().nullable().optional(),
  net_income: z.number().nullable().optional(),
  debt_to_equity: z.number().nullable().optional(),
  roe: z.number().nullable().optional(),
  roa: z.number().nullable().optional(),
  operating_margin: z.number().nullable().optional(),
  profit_margin: z.number().nullable().optional(),
  revenue_growth: z.number().nullable().optional(),
  earnings_growth: z.number().nullable().optional(),
  current_ratio: z.number().nullable().optional(),
  quick_ratio: z.number().nullable().optional(),
  price_to_sales: z.number().nullable().optional(),
  price_to_cash_flow: z.number().nullable().optional(),
  enterprise_value: z.number().nullable().optional(),
  ev_to_revenue: z.number().nullable().optional(),
  ev_to_ebitda: z.number().nullable().optional(),
  free_cash_flow: z.number().nullable().optional(),
  country: z.string(),
  market: z.string(),
  date: z.string(),
  best_k_value: z.number().nullable().optional(), // 새로 추가된 Best k값
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
export type DailyStockData = typeof dailyStockData.$inferSelect;
export type InsertDailyStockData = typeof dailyStockData.$inferInsert;
export type DataCollectionLog = typeof dataCollectionLog.$inferSelect;
export type InsertDataCollectionLog = typeof dataCollectionLog.$inferInsert;
