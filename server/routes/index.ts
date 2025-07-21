// ✅ server/routes/index.ts

import express from "express";
import apiRoutes from "./api";

export async function registerRoutes(app: express.Express) {
  const server = require("http").createServer(app);

  // 이 줄이 핵심입니다!
  app.use("/api", apiRoutes);

  return server;
}
