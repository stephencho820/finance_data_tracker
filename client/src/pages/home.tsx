"use client";

import { useEffect, useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import DataCollectionForm from "@/components/data-collection-form";
import MarketCapSection from "@/components/market-cap-section";
import { QuickStats } from "@/components/quick-stats";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartLine } from "lucide-react";
import CollectionSteps from "@/components/collection-status"; // ✅ 수집 상태 단계 컴포넌트 추가
import type { MarketCapRow } from "@/components/market-cap-section";

const API_BASE = location.origin;

export default function Home() {
  const [stockData, setStockData] = useState<MarketCapRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchInitialData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/market-latest`);
      const json = await res.json();

      if (json.success) {
        setStockData(json.data || []);
      } else {
        console.warn("🚫 초기 데이터 없음:", json.message);
      }
    } catch (err) {
      console.error("❌ 초기 시가총액 데이터 로드 실패:", err);
    }
  };

  // ✅ 최초 마운트 시 1회 실행
  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleDataCollected = (data: MarketCapRow[]) => {
    console.log("✅ handleDataCollected 실행됨");
    setStockData(data);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <ChartLine className="text-blue-500 h-6 w-6" />
              <h1 className="text-xl font-bold text-white">Simulator</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Accordion
          type="multiple"
          defaultValue={["data-collection"]}
          className="space-y-4"
        >
          {/* Accordion 1 - 데이터 수집 */}
          <AccordionItem value="data-collection">
            <AccordionTrigger className="text-white text-lg">
              Collection & Best k Calculation
            </AccordionTrigger>
            <AccordionContent>
              <Card className="bg-slate-900 border-slate-700 mb-4">
                <CardHeader>
                  <CardTitle className="text-white">Collect Agent</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* ✅ 상태 단계 UI 추가 */}

                  <DataCollectionForm
                    mode="collect"
                    collectedData={stockData}
                    onDataCollected={handleDataCollected}
                  />

                  {/* ✅ KOSPI / KOSDAQ 필터링 + 페이지네이션 섹션 */}
                  <MarketCapSection data={stockData} />
                </CardContent>
              </Card>
            </AccordionContent>
          </AccordionItem>

          {/* Accordion 2 - Simulator */}
          <AccordionItem value="simulator">
            <AccordionTrigger className="text-white text-lg">
              Simulator
            </AccordionTrigger>
            <AccordionContent>
              <Card className="bg-slate-900 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">시뮬레이션 설정</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataCollectionForm
                    mode="simulate"
                    collectedData={stockData}
                    onDataCollected={handleDataCollected}
                  />
                  <QuickStats />
                </CardContent>
              </Card>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </main>
    </div>
  );
}
