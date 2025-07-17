#!/usr/bin/env python3

import subprocess

if __name__ == "__main__":
    print("[RUN] collector_market_cap.py 실행")
    subprocess.run(["python3", "server/services/collector_market_cap.py"],
                   check=True)

    print("[RUN] collector.py 실행")
    subprocess.run(["python3", "server/services/collector.py"], check=True)

    print("✅ All collectors completed!")
