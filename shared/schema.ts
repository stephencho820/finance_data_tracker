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
});

export const stockDataResponse = z.object({
  symbol: z.string(),
  name: z.string(),
  price: z.number().nullable(),
  change: z.number().nullable(),
  changePercent: z.number().nullable(),
  volume: z.number().nullable(),
  marketCap: z.string().nullable(),
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
