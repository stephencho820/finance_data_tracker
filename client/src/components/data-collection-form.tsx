"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import CollectionSteps from "@/components/collection-steps";

type StepStatus = "done" | "loading" | "pending";

const endpoints = [
  "/api/collect-market-cap",
  "/api/collect-ohlcv",
  "/api/calculate-best-k",
];
const messages = [
  "시가총액 수집 완료",
  "1Y OHLCV 수집 완료",
  "Best K 계산 완료",
];

export default function DataCollectionForm({
  collectedData,
  onDataCollected,
  mode,
}: {
  collectedData: any[];
  onDataCollected: (data: any[]) => void;
  mode: "collect" | "simulate";
}) {
  const { toast } = useToast();

  const [statuses, setStatuses] = useState<StepStatus[]>([
    "pending",
    "pending",
    "pending",
  ]);
  const [updateDates, setUpdateDates] = useState<{
    marketCap?: string;
    ohlcv?: string;
    bestK?: string;
  }>({});

  const [loadingStep, setLoadingStep] = useState<number | null>(null);
  const [progress, setProgress] = useState<number>(0);

  const fetchCollectionStatus = async () => {
    try {
      const res = await fetch("/api/collection-status");
      const json = await res.json();
      if (!json.success) return;

      const data = json.data;
      const steps: StepStatus[] = ["pending", "pending", "pending"];
      if (data.marketCapDone) steps[0] = "done";
      if (data.ohlcvDone) steps[1] = "done";
      if (data.bestKDone) steps[2] = "done";

      setStatuses(steps);
      setUpdateDates({
        marketCap: data.marketCapDate,
        ohlcv: data.ohlcvDate,
        bestK: data.bestKDone ? data.marketCapDate : undefined,
      });
    } catch (e) {
      console.error("❌ 상태 확인 실패:", e);
    }
  };

  useEffect(() => {
    fetchCollectionStatus();
  }, []);

  useEffect(() => {
    if (loadingStep === null) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/collect-progress");
        const json = await res.json();
        setProgress(Math.floor((json.current / json.total) * 100));
      } catch (e) {
        console.error("❌ 진행률 확인 실패:", e);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [loadingStep]);

  const runStep = async (stepIndex: number) => {
    setLoadingStep(stepIndex);
    setProgress(0);
    try {
      const res = await fetch(endpoints[stepIndex], { method: "POST" });
      const json = await res.json();
      if (!json.success) throw new Error(json.message || "실패");

      toast({ title: messages[stepIndex] });

      if (stepIndex <= 1) {
        const latest = await fetch("/api/market-latest");
        const result = await latest.json();
        if (result.success) onDataCollected(result.data);
      }

      await fetchCollectionStatus();
    } catch (err: any) {
      toast({
        title: "에러",
        description: err.message || "실행 중 오류 발생",
        variant: "destructive",
      });
    } finally {
      setLoadingStep(null);
    }
  };

  return (
    <div className="bg-slate-900 p-6 space-y-6">
      <CollectionSteps
        statuses={statuses.map((s, i) => (i === loadingStep ? "loading" : s))}
        dates={updateDates}
        onStepClick={(i) => {
          if (loadingStep === null) runStep(i);
        }}
      />

      {loadingStep !== null && (
        <div className="flex flex-col gap-2 items-start">
          <Progress value={progress} className="h-2 w-full" />
          <div className="text-xs text-slate-400">{progress}% 완료</div>
        </div>
      )}
    </div>
  );
}
