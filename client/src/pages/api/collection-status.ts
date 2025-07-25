"use client";

import { useEffect, useState } from "react";

export default function CollectionSteps() {
  const [status, setStatus] = useState({
    marketCapDone: false,
    ohlcvDone: false,
    bestKDone: false,
    marketCapDate: "",
    ohlcvDate: "",
  });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/collection-status");
        const json = await res.json();
        if (json.success) {
          setStatus(json.data);
        } else {
          console.warn("🚫 상태 조회 실패:", json.message);
        }
      } catch (err) {
        console.error("❌ 상태 확인 실패:", err);
      }
    };

    fetchStatus();
  }, []);

  const Step = ({ label, done }: { label: string; done: boolean }) => (
    <div className="flex flex-col items-center w-1/3">
      <div
        className={`rounded-full w-5 h-5 mb-1 ${
          done ? "bg-green-400" : "bg-slate-500"
        }`}
      />
      <div className="text-sm text-slate-300 text-center">{label}</div>
    </div>
  );

  return (
    <div className="mb-6">
      {/* ✅ 수집 단계 상태 */}
      <div className="flex justify-between items-center space-x-2 px-2 mb-2">
        <Step label="시가총액 수집" done={status.marketCapDone} />
        <Step label="OHLCV 수집" done={status.ohlcvDone} />
        <Step label="Best K 계산" done={status.bestKDone} />
      </div>

      {/* ✅ 수집일자 정보 */}
      <div className="text-sm text-slate-400 text-center">
        시가총액 수집일: {status.marketCapDate || "없음"} / OHLCV 수집일: {status.ohlcvDate || "없음"}
      </div>
    </div>
  );
}
