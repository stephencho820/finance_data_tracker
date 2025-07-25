"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { CheckCircle } from "lucide-react";

interface StatusInfo {
  step: number;
  marketCapDate?: string;
  ohlcvDate?: string;
  bestKDate?: string;
}

const steps = [
  "시가총액 수집",
  "OHLCV 수집",
  "Best K 계산",
  "시뮬레이션 완료",
  "실전매매 준비",
];

const API_BASE = location.origin;

export const CollectionProgressBar = () => {
  const [status, setStatus] = useState<StatusInfo>({ step: 0 });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/collection-status`);
        const json = await res.json();
        if (json.success) {
          setStatus(json);
        } else {
          console.warn("🚫 상태 조회 실패:", json.message);
        }
      } catch (err) {
        console.error("❌ 상태 확인 실패:", err);
      }
    };

    fetchStatus();
  }, []);

  const getLabel = (index: number) => {
    let date: string | undefined;
    if (index === 0) date = status.marketCapDate?.slice(0, 10);
    if (index === 1) date = status.ohlcvDate?.slice(0, 10);
    if (index === 2 && status.step >= 3) date = status.bestKDate?.slice(0, 10);
    return date ? `${steps[index]} (${date})` : steps[index];
  };

  return (
    <div className="space-y-2 mb-4">
      <div className="flex justify-between text-sm text-slate-400">
        {steps.map((label, index) => (
          <div key={index} className="flex-1 text-center">
            <div
              className={`font-semibold ${
                status.step > index ? "text-blue-400" : "text-slate-500"
              }`}
            >
              {getLabel(index)}
              {status.step > index && (
                <CheckCircle className="inline ml-1 w-4 h-4 text-green-400" />
              )}
            </div>
          </div>
        ))}
      </div>
      <Progress
        value={Math.floor((status.step / steps.length) * 100)}
        className="h-2"
      />
    </div>
  );
};
