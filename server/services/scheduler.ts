import * as cron from 'node-cron';
import { spawn } from 'child_process';
import path from 'path';
import { log } from '../vite';

export class DataCollectionScheduler {
  private static instance: DataCollectionScheduler;
  private tasks: Map<string, cron.ScheduledTask> = new Map();

  private constructor() {}

  public static getInstance(): DataCollectionScheduler {
    if (!DataCollectionScheduler.instance) {
      DataCollectionScheduler.instance = new DataCollectionScheduler();
    }
    return DataCollectionScheduler.instance;
  }

  public start() {
    // 매일 오전 8시에 KOSPI 데이터 수집
    const kospiTask = cron.schedule('0 8 * * *', () => {
      this.collectDailyData('KOSPI');
    }, {
      scheduled: true,
      timezone: "Asia/Seoul"
    });

    // 매일 오전 8시 5분에 KOSDAQ 데이터 수집
    const kosdaqTask = cron.schedule('5 8 * * *', () => {
      this.collectDailyData('KOSDAQ');
    }, {
      scheduled: true,
      timezone: "Asia/Seoul"
    });

    this.tasks.set('kospi', kospiTask);
    this.tasks.set('kosdaq', kosdaqTask);

    log('Data collection scheduler started');
    log('KOSPI data collection scheduled at 08:00 KST daily');
    log('KOSDAQ data collection scheduled at 08:05 KST daily');
  }

  public stop() {
    this.tasks.forEach((task, name) => {
      task.stop();
      log(`Stopped ${name} data collection task`);
    });
    this.tasks.clear();
  }

  private async collectDailyData(market: string) {
    return new Promise((resolve, reject) => {
      log(`Starting daily data collection for ${market}`);
      
      const pythonScript = path.join(__dirname, "daily-data-collector.py");
      const pythonProcess = spawn("python3", [pythonScript]);

      // 입력 데이터 전송
      pythonProcess.stdin.write(JSON.stringify({ market }));
      pythonProcess.stdin.end();

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        log(`[${market}] ${data.toString().trim()}`, 'scheduler');
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout);
            if (result.success) {
              log(`Daily data collection for ${market} completed successfully`);
              resolve(result);
            } else {
              log(`Daily data collection for ${market} failed: ${result.message}`);
              reject(new Error(result.message));
            }
          } catch (error) {
            log(`Failed to parse result for ${market}: ${error}`);
            reject(error);
          }
        } else {
          log(`Daily data collection for ${market} failed with code ${code}`);
          reject(new Error(`Process exited with code ${code}`));
        }
      });

      // 타임아웃 설정 (2시간)
      setTimeout(() => {
        pythonProcess.kill();
        reject(new Error('Data collection timeout'));
      }, 2 * 60 * 60 * 1000);
    });
  }

  // 수동 실행 메서드
  public async manualCollect(market: string) {
    return this.collectDailyData(market);
  }
}

export default DataCollectionScheduler;