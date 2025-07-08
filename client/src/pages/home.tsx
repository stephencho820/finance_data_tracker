import { useState } from "react";
import { DataCollectionForm } from "@/components/data-collection-form";
import { DataDisplay } from "@/components/data-display";
import { HistoricalData } from "@/components/historical-data";
import { QuickStats } from "@/components/quick-stats";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { type StockDataResponse } from "@shared/schema";
import { ChartLine, Moon, Sun, Settings } from "lucide-react";

export default function Home() {
  const [stockData, setStockData] = useState<StockDataResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { theme, setTheme } = useTheme();

  const handleDataCollected = (data: StockDataResponse[]) => {
    setStockData(data);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <ChartLine className="text-blue-500 text-2xl" />
                <h1 className="text-xl font-bold text-white">Trading Data Collector</h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setTheme(theme === "light" ? "dark" : "light")}
                className="hover:bg-slate-800"
              >
                {theme === "light" ? (
                  <Moon className="h-5 w-5 text-slate-400" />
                ) : (
                  <Sun className="h-5 w-5 text-slate-400" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="hover:bg-slate-800"
              >
                <Settings className="h-5 w-5 text-slate-400" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Data Collection Form */}
          <DataCollectionForm onDataCollected={handleDataCollected} />

          {/* Data Display */}
          <DataDisplay data={stockData} isLoading={isLoading} />

          {/* Historical Data */}
          <HistoricalData />

          {/* Quick Stats */}
          <QuickStats />
        </div>
      </main>
    </div>
  );
}
