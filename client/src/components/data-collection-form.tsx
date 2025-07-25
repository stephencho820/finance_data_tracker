// 📄 client/src/components/data-collection-form.tsx
"use client";

import { CollectionProgressBar } from "@/components/collection-progress-bar";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import CollectionSteps from "@/components/collection-steps";

export interface DataCollectionFormProps {
  collectedData: any[];
  onDataCollected: (data: any[]) => void;
  mode: "collect" | "simulate";
}

const API_BASE = location.origin;

export default function DataCollectionForm({
  collectedData,
  onDataCollected,
  mode,
}: DataCollectionFormProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0); // ✅ 단계 상태

  // ✅ 최초 렌더 시 상태 확인
  useEffect(() => {
    console.log("🧪 DataCollectionForm 렌더됨, mode:", mode);
    fetch(`${API_BASE}/api/collection-status`)
      .then((res) => res.json())
      .then((json) => {
        if (json.success) {
          setCurrentStep(json.step);
        } else {
          console.warn("❌ 상태 확인 실패:", json.message);
        }
      })
      .catch((err) => {
        console.error("❌ 상태 확인 실패:", err);
      });
  }, [mode]);

  // 🔁 수집 중일 때 퍼센트 업데이트
  useEffect(() => {
    if (!loading) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/collect-progress`);
        const data = await res.json();
        const pct = Math.floor((data.current / data.total) * 100);
        setProgress(pct);
      } catch (err) {
        console.error("❌ 진행률 폴링 실패:", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [loading]);

  const handleCollectData = async () => {
    setLoading(true);
    setProgress(0);
    setCurrentStep(0);

    try {
      // 1. collector 실행
      const response = await fetch(`${API_BASE}/api/collect-data`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const contentType = response.headers.get("content-type");
      if (!contentType || !contentType.includes("application/json")) {
        throw new Error("서버 응답이 JSON 형식이 아닙니다.");
      }

      const result = await response.json();

      if (!result.success) {
        toast({
          title: "데이터 수집 실패",
          description: result.message || "알 수 없는 오류",
          variant: "destructive",
        });
        return;
      }

      setCurrentStep(2); // ✅ OHLCV까지 완료 기준

      // 2. 최신 시가총액 데이터 받아오기
      const latestRes = await fetch(`${API_BASE}/api/market-latest`);
      const latestJson = await latestRes.json();

      if (!latestJson.success) {
        toast({
          title: "데이터 로드 실패",
          description:
            latestJson.message || "최신 데이터를 가져오지 못했습니다.",
          variant: "destructive",
        });
        return;
      }

      // 3. 테이블에 표시할 데이터 전달
      onDataCollected(latestJson.data || []);

      // ✅ best_k 여부에 따라 step 3 도달
      const hasBestK = latestJson.data.some((row: any) => row.best_k !== null);
      if (hasBestK) {
        setCurrentStep(3);
      }

      toast({
        title: "데이터 수집 완료",
        description: result.message || "수집이 완료되었습니다.",
      });
    } catch (error: any) {
      toast({
        title: "에러",
        description: error?.message || "collector 실행 중 오류가 발생했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-slate-900 border-slate-700 p-6 space-y-4">
      {/* ✅ 수집 단계 표시 */}
      <CollectionSteps currentStep={currentStep} />

      {mode === "collect" && (
        <div className="flex flex-col gap-3">
          <Button
            type="button"
            onClick={handleCollectData}
            className="bg-blue-600 text-white hover:bg-blue-700"
            disabled={loading}
          >
            {loading ? "수집 중입니다..." : "Collect Fish"}
          </Button>

          {loading && (
            <>
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-slate-400">{progress}% 완료</div>
            </>
          )}
        </div>
      )}
    </Card>
  );
}
