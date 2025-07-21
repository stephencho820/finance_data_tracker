"use client";

import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import DataCollectionForm from "@/components/data-collection-form"; // ✅ default import
import { DataDisplay } from "@/components/data-display";
import { QuickStats } from "@/components/quick-stats";
import { type StockDataResponse } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartLine } from "lucide-react";

export default function Home() {
  const [stockData, setStockData] = useState<StockDataResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleDataCollected = (data: StockDataResponse[]) => {
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
        <Accordion type="multiple" className="space-y-4">
          {/* Accordion 1 - 데이터 수집 */}
          <AccordionItem value="data-collection">
            <AccordionTrigger className="text-white text-lg">
              데이터 수집
            </AccordionTrigger>
            <AccordionContent>
              <Card className="bg-slate-900 border-slate-700 mb-4">
                <CardHeader>
                  <CardTitle className="text-white">데이터 수집</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataCollectionForm
                    mode="collect"
                    collectedData={stockData}
                    onDataCollected={handleDataCollected}
                  />
                  <DataDisplay data={stockData} isLoading={isLoading} />
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
