"use client";

import { CheckCircle, Loader2 } from "lucide-react";

// ✅ 이 컴포넌트는 📄 client/src/components/collection-steps.tsx 에 위치해야 합니다

const steps = [
  "시가총액 수집",
  "OHLCV 수집",
  "Best K 계산",
  "시뮬레이터 설정",
  "실전 매매 준비",
] as const;

interface CollectionStepsProps {
  currentStep: number; // ✅ 현재 단계는 외부에서 props로 전달받습니다
}

export default function CollectionSteps({ currentStep }: CollectionStepsProps) {
  const getStatus = (index: number) => {
    if (index < currentStep) return "done";
    if (index === currentStep) return "active";
    return "pending";
  };

  return (
    <div className="flex items-center justify-between gap-2 mb-6">
      {steps.map((label, index) => {
        const status = getStatus(index);
        const isLast = index === steps.length - 1;

        return (
          <div key={index} className="flex items-center gap-2 w-full">
            {/* Step Circle */}
            <div className="flex flex-col items-center">
              <div
                className={`rounded-full w-6 h-6 flex items-center justify-center
                  ${
                    status === "done"
                      ? "bg-green-500 text-white"
                      : status === "active"
                        ? "border-2 border-blue-500 text-blue-500"
                        : "border-2 border-slate-600 text-slate-400"
                  }
                `}
              >
                {status === "done" ? (
                  <CheckCircle size={16} className="text-white" />
                ) : status === "active" ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  index + 1
                )}
              </div>
              <span className="text-xs mt-1 text-center text-slate-300 w-20">
                {label}
              </span>
            </div>

            {/* Divider */}
            {!isLast && <div className="flex-1 h-px bg-slate-700" />}
          </div>
        );
      })}
    </div>
  );
}
