"""
MySQL 기반 일일 데이터 수집 스케줄러
매일 오전 8시에 daily-stock-collector-mysql.py 실행
"""

import * as cron from 'node-cron';
import { spawn } from 'child_process';
import { promises as fs } from 'fs';
import path from 'path';

export class MySQLDataCollectionScheduler {
  private static instance: MySQLDataCollectionScheduler;
  private tasks: Map<string, cron.ScheduledTask> = new Map();

  private constructor() {}

  public static getInstance(): MySQLDataCollectionScheduler {
    if (!MySQLDataCollectionScheduler.instance) {
      MySQLDataCollectionScheduler.instance = new MySQLDataCollectionScheduler();
    }
    return MySQLDataCollectionScheduler.instance;
  }

  public start() {
    console.log('[MySQL Scheduler] Starting MySQL data collection scheduler...');
    
    // 매일 오전 8시 (KST) 실행
    const dailyTask = cron.schedule('0 8 * * *', async () => {
      console.log('[MySQL Scheduler] Starting daily data collection...');
      await this.collectDailyData();
    }, {
      scheduled: true,
      timezone: 'Asia/Seoul'
    });

    this.tasks.set('daily-collection', dailyTask);
    console.log('[MySQL Scheduler] Daily data collection scheduled at 08:00 KST');
  }

  public stop() {
    console.log('[MySQL Scheduler] Stopping all scheduled tasks...');
    this.tasks.forEach((task, name) => {
      task.destroy();
      console.log(`[MySQL Scheduler] Stopped task: ${name}`);
    });
    this.tasks.clear();
  }

  private async collectDailyData(): Promise<void> {
    const scriptPath = path.join(__dirname, 'daily-stock-collector-mysql.py');
    
    try {
      console.log('[MySQL Scheduler] Executing daily data collection script...');
      
      // Python 스크립트 실행
      const pythonProcess = spawn('python3', [scriptPath], {
        stdio: 'pipe',
        env: {
          ...process.env,
          // MySQL 연결 정보 환경변수 설정
          DB_HOST: process.env.DB_HOST || 'localhost',
          DB_NAME: process.env.DB_NAME || 'stock_db',
          DB_USER: process.env.DB_USER || 'root',
          DB_PASSWORD: process.env.DB_PASSWORD || '',
          DB_PORT: process.env.DB_PORT || '3306'
        }
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log(`[MySQL Scheduler] ${data.toString().trim()}`);
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error(`[MySQL Scheduler] ERROR: ${data.toString().trim()}`);
      });

      pythonProcess.on('close', async (code) => {
        if (code === 0) {
          console.log('[MySQL Scheduler] Daily data collection completed successfully');
          await this.logCollectionResult('SUCCESS', null, stdout);
        } else {
          console.error(`[MySQL Scheduler] Daily data collection failed with code ${code}`);
          await this.logCollectionResult('FAILED', stderr, stdout);
        }
      });

      pythonProcess.on('error', async (error) => {
        console.error(`[MySQL Scheduler] Process error: ${error.message}`);
        await this.logCollectionResult('ERROR', error.message, stdout);
      });

    } catch (error) {
      console.error(`[MySQL Scheduler] Script execution error: ${error}`);
      await this.logCollectionResult('ERROR', error instanceof Error ? error.message : 'Unknown error', '');
    }
  }

  private async logCollectionResult(status: string, error: string | null, output: string): Promise<void> {
    const logEntry = {
      timestamp: new Date().toISOString(),
      status,
      error,
      output: output.slice(-1000), // 마지막 1000자만 저장
    };

    const logPath = '/tmp/mysql_collection_log.json';
    
    try {
      let logs = [];
      try {
        const existingLogs = await fs.readFile(logPath, 'utf-8');
        logs = JSON.parse(existingLogs);
      } catch {
        // 파일이 없으면 새로 생성
      }
      
      logs.push(logEntry);
      
      // 최근 100개 로그만 유지
      if (logs.length > 100) {
        logs = logs.slice(-100);
      }
      
      await fs.writeFile(logPath, JSON.stringify(logs, null, 2));
      
    } catch (logError) {
      console.error(`[MySQL Scheduler] Failed to write log: ${logError}`);
    }
  }

  public async manualCollect(): Promise<void> {
    console.log('[MySQL Scheduler] Manual data collection triggered');
    await this.collectDailyData();
  }

  public async getCollectionLogs(): Promise<any[]> {
    const logPath = '/tmp/mysql_collection_log.json';
    
    try {
      const logs = await fs.readFile(logPath, 'utf-8');
      return JSON.parse(logs);
    } catch {
      return [];
    }
  }
}

// 싱글톤 인스턴스 내보내기
export const mysqlScheduler = MySQLDataCollectionScheduler.getInstance();