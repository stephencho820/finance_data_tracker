import { Express } from "express";
import apiRouter from "./api";

export async function registerRoutes(app: Express) {
  app.use("/api", apiRouter);
  return app;
}
