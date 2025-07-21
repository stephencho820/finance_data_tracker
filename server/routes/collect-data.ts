// server/routes/collect-data.ts
import express from "express";
import { exec } from "child_process";
import path from "path";

const router = express.Router();

router.post("/", async (req, res) => {
  const scriptPath = path.resolve(__dirname, "../services/collector.py");
  const command = `python3 ${scriptPath}`; // 또는 Windows면 python

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error("collector.py 실행 오류:", error);
      return res.status(500).json({
        success: false,
        message: "collector.py 실행 중 오류 발생",
        error: stderr,
      });
    }

    console.log("collector.py 실행 결과:", stdout);
    res.status(200).json({
      success: true,
      message: "데이터 수집 완료",
      output: stdout,
    });
  });
});

export default router;
