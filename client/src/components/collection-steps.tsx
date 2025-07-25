"use client";

import { CheckCircle, Loader2 } from "lucide-react";

const steps = ["시가총액 수집", "1Y 수집", "Best K 계산"] as const;

type StepStatus = "done" | "loading" | "pending";

interface CollectionStepsProps {
  statuses: StepStatus[];
  dates?: {
    marketCap?: string;
    ohlcv?: string;
    bestK?: string;
  };
  onStepClick?: (index: number) => void;
}

export default function CollectionSteps({
  statuses,
  dates,
  onStepClick,
}: CollectionStepsProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
  };

  const getDateLabel = (index: number) => {
    switch (index) {
      case 0:
        return dates?.marketCap
          ? `${formatDate(dates.marketCap)} update 완료`
          : null;
      case 1:
        return dates?.ohlcv ? `${formatDate(dates.ohlcv)} update 완료` : null;
      case 2:
        return dates?.bestK ? `${formatDate(dates.bestK)} update 완료` : null;
      default:
        return null;
    }
  };

  return (
    <div className="flex justify-center mb-6">
      <div className="flex items-start gap-0">
        {steps.map((label, index) => {
          const status = statuses[index];
          const isClickable = status === "pending" && onStepClick;

          return (
            <div key={index} className="flex items-start">
              {/* Step Item */}
              <div className="flex flex-col items-center gap-2 min-w-[90px]">
                <button
                  onClick={() => isClickable && onStepClick?.(index)}
                  disabled={!isClickable}
                  className="flex flex-col items-center bg-transparent border-none focus:outline-none cursor-pointer"
                >
                  <div
                    className={`rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold
                      ${
                        status === "done"
                          ? "bg-green-500 text-white"
                          : status === "loading"
                            ? "bg-blue-500 text-white animate-spin"
                            : "bg-slate-600 text-white hover:bg-white hover:text-slate-800"
                      }
                    `}
                  >
                    {status === "done" ? (
                      <CheckCircle size={16} className="text-white" />
                    ) : status === "loading" ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      index + 1
                    )}
                  </div>

                  <span className="text-xs mt-1 text-center text-slate-300 w-24">
                    {label}
                  </span>

                  {getDateLabel(index) && (
                    <span className="text-[10px] text-slate-500 mt-1">
                      {getDateLabel(index)}
                    </span>
                  )}
                </button>
              </div>

              {/* Divider (except last) */}
              {index < steps.length - 1 && (
                <div className="flex items-center mt-[10px]">
                  <div className="w-8 h-px bg-slate-700 mx-2" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
