"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import CollectionSteps from "@/components/collection-steps";
import {
  Calendar,
  Settings,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

type StepStatus = "done" | "loading" | "pending";

interface PeriodOption {
  value: string;
  label: string;
  description: string;
}

interface MarketOption {
  value: string;
  label: string;
  description: string;
}

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
  const [isStepEnabled, setIsStepEnabled] = useState<boolean[]>([
    true, // 시가총액 수집은 항상 가능
    false, // 1Y 수집은 시가총액 완료 후 가능
    false, // Best K는 1Y 수집 완료 후 가능
  ]);

  // Best K 설정 상태
  const [showBestKSettings, setShowBestKSettings] = useState<boolean>(false);
  const [selectedPeriod, setSelectedPeriod] = useState<string>("month_1");
  const [selectedMarket, setSelectedMarket] = useState<string>("ALL");
  const [customStartDate, setCustomStartDate] = useState<string>("");
  const [customEndDate, setCustomEndDate] = useState<string>("");
  const [periods, setPeriods] = useState<PeriodOption[]>([]);
  const [markets, setMarkets] = useState<MarketOption[]>([]);
  const [bestKProgress, setBestKProgress] = useState<{
    current: number;
    total: number;
    percent: number;
    isRunning: boolean;
  }>({ current: 0, total: 200, percent: 0, isRunning: false });

  // 기간 및 시장 옵션 로드
  useEffect(() => {
    const loadBestKOptions = async () => {
      try {
        const res = await fetch("/api/best-k-periods");
        const json = await res.json();
        if (json.success) {
          setPeriods(json.data.periods);
          setMarkets(json.data.markets);
        }
      } catch (e) {
        console.error("Best K 옵션 로드 실패:", e);
        // 임시로 하드코딩된 옵션 사용
        setPeriods([
          {
            value: "days_3",
            label: "최근 3일",
            description: "최근 3일간의 데이터 기준",
          },
          {
            value: "week_1",
            label: "1주일",
            description: "최근 1주일간의 데이터 기준",
          },
          {
            value: "month_1",
            label: "1개월",
            description: "최근 1개월간의 데이터 기준",
          },
          {
            value: "month_3",
            label: "3개월",
            description: "최근 3개월간의 데이터 기준",
          },
          {
            value: "quarter",
            label: "분기",
            description: "최근 분기(3개월)간의 데이터 기준",
          },
          {
            value: "half_year",
            label: "반기",
            description: "최근 반기(6개월)간의 데이터 기준",
          },
          {
            value: "year_1",
            label: "1년",
            description: "최근 1년간의 데이터 기준",
          },
          {
            value: "custom",
            label: "사용자 지정",
            description: "직접 시작일과 종료일을 선택",
          },
        ]);
        setMarkets([
          { value: "ALL", label: "전체", description: "KOSPI + KOSDAQ 전체" },
          { value: "KOSPI", label: "KOSPI", description: "KOSPI 시장만" },
          { value: "KOSDAQ", label: "KOSDAQ", description: "KOSDAQ 시장만" },
        ]);
      }
    };
    loadBestKOptions();
  }, []);

  const fetchCollectionStatus = async () => {
    try {
      const res = await fetch("/api/collection-status");
      const json = await res.json();
      if (!json.success) return;

      const data = json.data;
      const steps: StepStatus[] = ["pending", "pending", "pending"];
      const enabledSteps = [true, false, false]; // 기본값

      // 1단계: 시가총액 수집 상태
      if (data.marketCapDone) {
        steps[0] = "done";
        enabledSteps[1] = true; // 1Y 수집 활성화
      }

      // 2단계: OHLCV 수집 상태
      if (data.ohlcvDone) {
        steps[1] = "done";
        enabledSteps[2] = true; // Best K 계산 활성화
      }

      // 3단계: Best K 계산 상태
      if (data.bestKDone) {
        steps[2] = "done";
      }

      setStatuses(steps);
      setIsStepEnabled(enabledSteps);
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

    // 컴포넌트 마운트 시 백엔드 실행 상태 확인
    const checkBackendStatus = async () => {
      try {
        const res = await fetch("/api/best-k-progress");
        const json = await res.json();

        // 백엔드에서 Best K가 실행 중이면 프런트엔드 상태 동기화
        if (json.isRunning) {
          setLoadingStep(2);
          setProgress(json.percent);
          setBestKProgress(json);
          console.log("🔄 백엔드 Best K 실행 상태 감지, 프런트엔드 동기화");
        }
      } catch (e) {
        console.error("❌ 백엔드 상태 확인 실패:", e);
      }
    };

    checkBackendStatus();
  }, []);

  // 일반 데이터 수집 진행률 추적
  useEffect(() => {
    if (loadingStep === null || loadingStep === 2) return; // Best K는 별도 추적
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

  // Best K 진행률 추적
  useEffect(() => {
    let interval: NodeJS.Timeout;

    const checkBestKProgress = async () => {
      try {
        const res = await fetch("/api/best-k-progress");
        const json = await res.json();
        setBestKProgress(json);

        // 백엔드에서 실행 중이면 프런트엔드도 동기화
        if (json.isRunning && loadingStep !== 2) {
          setLoadingStep(2);
          setProgress(json.percent);
        } else if (!json.isRunning && loadingStep === 2) {
          setLoadingStep(null);
          // 완료 후 상태 재확인
          await fetchCollectionStatus();
        }

        if (loadingStep === 2) {
          setProgress(json.percent);
        }
      } catch (e) {
        console.error("❌ Best K 진행률 확인 실패:", e);
      }
    };

    // 항상 실행 (loadingStep과 관계없이)
    interval = setInterval(checkBestKProgress, 1000);

    // 컴포넌트 마운트 시 즉시 한 번 확인
    checkBestKProgress();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loadingStep]); // loadingStep 의존성 추가

  const runStep = async (stepIndex: number) => {
    // 단계가 비활성화되어 있으면 실행하지 않음
    if (!isStepEnabled[stepIndex]) {
      toast({
        title: "단계 실행 불가",
        description: "이전 단계를 먼저 완료해주세요.",
        variant: "destructive",
      });
      return;
    }

    setLoadingStep(stepIndex);
    setProgress(0);

    try {
      let requestBody = {};

      // Best K 계산인 경우 추가 파라미터 전송
      if (stepIndex === 2) {
        requestBody = {
          period: selectedPeriod,
          market: selectedMarket,
          ...(selectedPeriod === "custom" && {
            startDate: customStartDate,
            endDate: customEndDate,
          }),
        };

        // 커스텀 기간 검증
        if (
          selectedPeriod === "custom" &&
          (!customStartDate || !customEndDate)
        ) {
          toast({
            title: "설정 오류",
            description:
              "사용자 지정 기간을 선택한 경우 시작일과 종료일을 모두 입력해주세요.",
            variant: "destructive",
          });
          setLoadingStep(null);
          return;
        }
      }

      const res = await fetch(endpoints[stepIndex], {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      const json = await res.json();
      if (!json.success) throw new Error(json.message || "실패");

      toast({
        title: messages[stepIndex],
        description:
          stepIndex === 2 && json.data
            ? `${json.data.updated_symbols}개 종목 업데이트 완료`
            : undefined,
      });

      // 데이터 수집 단계에서는 최신 데이터 조회
      if (stepIndex <= 1) {
        const latest = await fetch("/api/market-latest");
        const result = await latest.json();
        if (result.success) onDataCollected(result.data);
      }

      // 상태 재확인 (다음 단계 활성화 체크)
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

  const handleStepClick = (stepIndex: number) => {
    if (loadingStep !== null) return;

    // 비활성화된 단계 클릭 시 안내 메시지
    if (!isStepEnabled[stepIndex]) {
      const stepNames = ["시가총액 수집", "1Y OHLCV 수집", "Best K 계산"];
      const prevStepName = stepNames[stepIndex - 1];

      toast({
        title: `${stepNames[stepIndex]} 비활성화`,
        description: `${prevStepName}을 먼저 완료해주세요.`,
        variant: "destructive",
      });
      return;
    }

    runStep(stepIndex);
  };

  const getSelectedPeriodInfo = () => {
    return periods.find((p) => p.value === selectedPeriod);
  };

  const getSelectedMarketInfo = () => {
    return markets.find((m) => m.value === selectedMarket);
  };

  return (
    <div className="bg-slate-900 p-6 space-y-6">
      <CollectionSteps
        statuses={statuses.map((s, i) => (i === loadingStep ? "loading" : s))}
        dates={updateDates}
        onStepClick={handleStepClick}
        enabledSteps={isStepEnabled} // 단계별 활성화 상태 전달
      />

      {/* Best K 설정 버튼 - 항상 표시 */}
      <div className="flex items-center justify-between bg-slate-800 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <TrendingUp className="text-blue-400" size={20} />
          <div>
            <h3 className="text-white font-medium">Best K 계산 설정</h3>
            <p className="text-slate-400 text-sm">
              {showBestKSettings
                ? "설정을 조정하고 계산을 시작하세요"
                : "기간과 시장을 설정하여 Best K 값을 계산합니다"}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowBestKSettings(!showBestKSettings)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
        >
          <Settings size={16} />
          <span>{showBestKSettings ? "설정 숨기기" : "설정 열기"}</span>
          {showBestKSettings ? (
            <ChevronUp size={16} />
          ) : (
            <ChevronDown size={16} />
          )}
        </button>
      </div>

      {/* Best K 설정 패널 */}
      {showBestKSettings && (
        <Card className="bg-slate-800 border-slate-700">
          <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TrendingUp className="text-blue-400" size={20} />
                <h3 className="text-lg font-semibold text-white">
                  Best K 계산 설정
                </h3>
              </div>
              <button
                onClick={() => setShowBestKSettings(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                {showBestKSettings ? (
                  <ChevronUp size={20} />
                ) : (
                  <ChevronDown size={20} />
                )}
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 기간 선택 */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-slate-300 flex items-center">
                  <Calendar className="mr-2" size={16} />
                  분석 기간 선택
                </h4>

                <div className="grid grid-cols-2 gap-2">
                  {periods.map((period) => (
                    <label
                      key={period.value}
                      className={`
                        relative cursor-pointer p-3 border rounded-lg transition-all duration-200 text-sm
                        ${
                          selectedPeriod === period.value
                            ? "border-blue-500 bg-blue-500/10 ring-1 ring-blue-400/30"
                            : "border-slate-600 hover:border-slate-500 hover:bg-slate-700/50"
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="period"
                        value={period.value}
                        checked={selectedPeriod === period.value}
                        onChange={(e) => setSelectedPeriod(e.target.value)}
                        className="sr-only"
                      />
                      <div className="text-white font-medium">
                        {period.label}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {period.description}
                      </div>
                    </label>
                  ))}
                </div>

                {/* 커스텀 날짜 선택 */}
                {selectedPeriod === "custom" && (
                  <div className="mt-4 p-4 bg-slate-700/50 rounded-lg space-y-3">
                    <h5 className="text-sm font-medium text-slate-300">
                      날짜 범위 설정
                    </h5>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">
                          시작일
                        </label>
                        <input
                          type="date"
                          value={customStartDate}
                          onChange={(e) => setCustomStartDate(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">
                          종료일
                        </label>
                        <input
                          type="date"
                          value={customEndDate}
                          onChange={(e) => setCustomEndDate(e.target.value)}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-md text-sm text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 시장 선택 및 실행 */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-slate-300 flex items-center">
                  <Settings className="mr-2" size={16} />
                  대상 시장 선택
                </h4>

                <div className="space-y-2">
                  {markets.map((market) => (
                    <label
                      key={market.value}
                      className={`
                        relative cursor-pointer p-3 border rounded-lg transition-all duration-200 block
                        ${
                          selectedMarket === market.value
                            ? "border-green-500 bg-green-500/10 ring-1 ring-green-400/30"
                            : "border-slate-600 hover:border-slate-500 hover:bg-slate-700/50"
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="market"
                        value={market.value}
                        checked={selectedMarket === market.value}
                        onChange={(e) => setSelectedMarket(e.target.value)}
                        className="sr-only"
                      />
                      <div className="text-sm font-medium text-white">
                        {market.label}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {market.description}
                      </div>
                    </label>
                  ))}
                </div>

                {/* 선택 정보 요약 */}
                <div className="bg-blue-500/10 border border-blue-500/30 p-3 rounded-lg">
                  <h5 className="text-sm font-medium text-blue-300 mb-2">
                    선택 정보
                  </h5>
                  <div className="text-xs text-blue-200 space-y-1">
                    <div>
                      <strong>기간:</strong> {getSelectedPeriodInfo()?.label}
                    </div>
                    <div>
                      <strong>시장:</strong> {getSelectedMarketInfo()?.label}
                    </div>
                    {selectedPeriod === "custom" &&
                      customStartDate &&
                      customEndDate && (
                        <div>
                          <strong>날짜:</strong> {customStartDate} ~{" "}
                          {customEndDate}
                        </div>
                      )}
                  </div>
                </div>

                {/* 실행 버튼 */}
                <button
                  onClick={() => runStep(2)}
                  disabled={
                    loadingStep !== null ||
                    (selectedPeriod === "custom" &&
                      (!customStartDate || !customEndDate))
                  }
                  className={`
                    w-full py-3 px-4 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center
                    ${
                      loadingStep !== null
                        ? "bg-slate-600 text-slate-400 cursor-not-allowed"
                        : "bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg"
                    }
                  `}
                >
                  <TrendingUp className="mr-2" size={16} />
                  Best K 값 계산 시작
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 진행률 표시 */}
      {(loadingStep !== null || bestKProgress.isRunning) && (
        <div className="flex flex-col gap-2 items-start">
          <Progress
            value={loadingStep === 2 ? bestKProgress.percent : progress}
            className="h-2 w-full"
          />
          <div className="text-xs text-slate-400">
            {loadingStep === 2 || bestKProgress.isRunning ? (
              <>
                Best K 계산 중: {bestKProgress.current}/{bestKProgress.total} (
                {bestKProgress.percent}% 완료)
              </>
            ) : (
              <>{progress}% 완료</>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
