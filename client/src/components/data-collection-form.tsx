import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { dataCollectionRequest, type DataCollectionRequest, type StockDataResponse } from "@shared/schema";
import { Calendar, ChartLine, Download, Flag, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataCollectionFormProps {
  onDataCollected: (data: StockDataResponse[]) => void;
}

const koreanMarkets = [
  { id: "kospi", name: "KOSPI", description: "코스피" },
  { id: "kosdaq", name: "KOSDAQ", description: "코스닥" },
  { id: "konex", name: "KONEX", description: "코넥스" },
  { id: "etf", name: "ETF", description: "상장지수펀드" },
];

const usMarkets = [
  { id: "sp500", name: "S&P 500", description: "^GSPC" },
  { id: "nasdaq", name: "NASDAQ", description: "^IXIC" },
  { id: "dow", name: "Dow Jones", description: "^DJI" },
  { id: "russell", name: "Russell 2000", description: "^RUT" },
];

export function DataCollectionForm({ onDataCollected }: DataCollectionFormProps) {
  const [selectedCountry, setSelectedCountry] = useState<"korea" | "usa">("korea");
  const [selectedMarket, setSelectedMarket] = useState("kospi");
  const { toast } = useToast();

  const form = useForm<DataCollectionRequest>({
    resolver: zodResolver(dataCollectionRequest),
    defaultValues: {
      startDate: "2024-01-01",
      endDate: "2024-12-31",
      country: "korea",
      market: "kospi",
    },
  });

  const collectDataMutation = useMutation({
    mutationFn: async (data: DataCollectionRequest) => {
      const response = await apiRequest("POST", "/api/collect-data", data);
      return response.json();
    },
    onSuccess: (result) => {
      if (result.success) {
        onDataCollected(result.data);
        toast({
          title: "데이터 수집 완료",
          description: result.message,
        });
      } else {
        toast({
          title: "데이터 수집 실패",
          description: result.message,
          variant: "destructive",
        });
      }
    },
    onError: (error) => {
      toast({
        title: "오류 발생",
        description: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.",
        variant: "destructive",
      });
    },
  });

  const onSubmit = (data: DataCollectionRequest) => {
    collectDataMutation.mutate({
      ...data,
      country: selectedCountry,
      market: selectedMarket,
    });
  };

  const handleCountryChange = (country: "korea" | "usa") => {
    setSelectedCountry(country);
    setSelectedMarket(country === "korea" ? "kospi" : "sp500");
  };

  const handleReset = () => {
    form.reset();
    setSelectedCountry("korea");
    setSelectedMarket("kospi");
    onDataCollected([]);
  };

  const currentMarkets = selectedCountry === "korea" ? koreanMarkets : usMarkets;

  return (
    <Card className="bg-slate-900 border-slate-700">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <ChartLine className="h-5 w-5 text-blue-500" />
          데이터 수집 설정
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Date Range */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="startDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">시작 날짜</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type="date"
                          {...field}
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                        <Calendar className="absolute right-3 top-3 h-4 w-4 text-slate-400" />
                      </div>
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="endDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">종료 날짜</FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type="date"
                          {...field}
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                        <Calendar className="absolute right-3 top-3 h-4 w-4 text-slate-400" />
                      </div>
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>

            {/* Country Selection */}
            <div>
              <Label className="text-slate-300 mb-2 block">국가 선택</Label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={selectedCountry === "korea" ? "default" : "outline"}
                  className={cn(
                    "flex items-center gap-2",
                    selectedCountry === "korea"
                      ? "bg-blue-600 hover:bg-blue-700 text-white"
                      : "bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                  )}
                  onClick={() => handleCountryChange("korea")}
                >
                  <Flag className="h-4 w-4" />
                  한국
                </Button>
                <Button
                  type="button"
                  variant={selectedCountry === "usa" ? "default" : "outline"}
                  className={cn(
                    "flex items-center gap-2",
                    selectedCountry === "usa"
                      ? "bg-blue-600 hover:bg-blue-700 text-white"
                      : "bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                  )}
                  onClick={() => handleCountryChange("usa")}
                >
                  <Flag className="h-4 w-4" />
                  미국
                </Button>
              </div>
            </div>

            {/* Market Selection */}
            <div>
              <Label className="text-slate-300 mb-4 block">시장 선택</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {currentMarkets.map((market) => (
                  <Button
                    key={market.id}
                    type="button"
                    variant="outline"
                    className={cn(
                      "h-auto p-4 flex-col items-start",
                      selectedMarket === market.id
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                    )}
                    onClick={() => setSelectedMarket(market.id)}
                  >
                    <div className="font-medium">{market.name}</div>
                    <div className="text-sm opacity-70">{market.description}</div>
                  </Button>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>
                  선택된 시장: <span className="text-blue-400 font-medium">
                    {currentMarkets.find(m => m.id === selectedMarket)?.name}
                  </span>
                </span>
              </div>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleReset}
                  className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  초기화
                </Button>
                <Button
                  type="submit"
                  disabled={collectDataMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {collectDataMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      수집 중...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      데이터 수집
                    </>
                  )}
                </Button>
              </div>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
