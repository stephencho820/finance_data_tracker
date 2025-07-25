// ✅ components/collection-status.tsx
"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface CollectionStatus {
  step: number;
  marketCapDate: string | null;
  ohlcvDate: string | null;
}

export default function CollectionSteps() {
  const [status, setStatus] = useState<CollectionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/collection-status");
        const json = await res.json();
        setStatus(json);
      } catch (err) {
        console.error("❌ 상태 확인 실패:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  const renderStep = (label: string, index: number) => {
    const complete = status?.step >= index;
    return (
      <div className="flex flex-col items-center w-full">
        <div
          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
            complete ? "bg-blue-500 text-white" : "bg-slate-600 text-slate-300"
          }`}
        >
          {index}
        </div>
        <span className="text-xs text-center mt-1 text-slate-300 whitespace-nowrap">
          {label}
        </span>
      </div>
    );
  };

  if (loading || !status) {
    return (
      <div className="flex gap-2 items-center text-slate-400 text-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> 상태 확인 중...
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* ✅ 단계 표시 */}
      <div className="flex justify-between items-center max-w-md mx-auto">
        {renderStep("시가총액 수집", 1)}
        <div className="flex-1 h-px bg-slate-600 mx-1" />
        {renderStep("OHLCV 수집", 2)}
        <div className="flex-1 h-px bg-slate-600 mx-1" />
        {renderStep("Best K 계산", 3)}
      </div>

      {/* ✅ 날짜 정보 */}
      <div className="text-sm text-slate-400 text-center">
        <div>
          시가총액 수집일: {status.marketCapDate || "없음"} / OHLCV 수집일:{" "}
          {status.ohlcvDate || "없음"}
        </div>
      </div>
    </div>
  );
}
