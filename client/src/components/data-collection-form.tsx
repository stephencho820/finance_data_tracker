import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { dataCollectionRequest, type DataCollectionRequest, type StockDataResponse } from "@shared/schema";
import { Calendar, ChartLine, Download, Flag, RotateCcw, Filter, Hash } from "lucide-react";
import { cn } from "@/lib/utils";

// 기본 날짜 계산 함수
function getDefaultDates() {
  const today = new Date();
  const endDate = new Date(today);
  endDate.setDate(today.getDate() - 1); // 어제
  
  const startDate = new Date(today);
  startDate.setDate(today.getDate() - 2); // 2일 전
  
  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0]
  };
}

interface DataCollectionFormProps {
  onDataCollected: (data: StockDataResponse[]) => void;
}

const koreanMarkets = [
  { id: "kospi", name: "KOSPI", description: "코스피" },
  { id: "kosdaq", name: "KOSDAQ", description: "코스닥" },
];

const sortOptions = [
  { id: "market_cap", name: "시가총액", description: "Market Cap" },
  { id: "volume", name: "거래량", description: "Volume" },
];

export function DataCollectionForm({ onDataCollected }: DataCollectionFormProps) {
  const [selectedCountry, setSelectedCountry] = useState<"korea" | "usa">("korea");
  const [selectedMarket, setSelectedMarket] = useState("kospi");
  const { toast } = useToast();

  const defaultDates = getDefaultDates();

  const form = useForm<DataCollectionRequest>({
    resolver: zodResolver(dataCollectionRequest),
    defaultValues: {
      startDate: defaultDates.startDate,
      endDate: defaultDates.endDate,
      country: "korea",
      market: "kospi",
      sortBy: "market_cap",
      limit: 500,
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
    setSelectedMarket("kospi");
  };

  const handleReset = () => {
    const defaultDates = getDefaultDates();
    form.reset({
      startDate: defaultDates.startDate,
      endDate: defaultDates.endDate,
      country: "korea",
      market: "kospi",
      sortBy: "market_cap",
      limit: 500,
    });
    setSelectedCountry("korea");
    setSelectedMarket("kospi");
    onDataCollected([]);
  };

  const currentMarkets = koreanMarkets;

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

            {/* Country Selection (Korea only) */}
            <div>
              <Label className="text-slate-300 mb-2 block">국가 선택</Label>
              <div className="grid grid-cols-1 gap-2">
                <Button
                  type="button"
                  variant="default"
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
                  disabled
                >
                  <Flag className="h-4 w-4" />
                  한국 (Korean Markets)
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

            {/* Sort and Limit Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="sortBy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300 flex items-center gap-2">
                      <Filter className="h-4 w-4" />
                      정렬 기준
                    </FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                          <SelectValue placeholder="정렬 기준 선택" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="bg-slate-800 border-slate-600">
                        {sortOptions.map((option) => (
                          <SelectItem key={option.id} value={option.id} className="text-white hover:bg-slate-700">
                            <div className="flex flex-col">
                              <span className="font-medium">{option.name}</span>
                              <span className="text-xs text-slate-400">{option.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="limit"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300 flex items-center gap-2">
                      <Hash className="h-4 w-4" />
                      수집 수량
                    </FormLabel>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type="number"
                          min="1"
                          max="500"
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                          className="bg-slate-800 border-slate-600 text-white"
                          placeholder="수집할 주식 수량 (기본값: 500)"
                        />
                        <span className="absolute right-3 top-3 text-xs text-slate-400">
                          개
                        </span>
                      </div>
                    </FormControl>
                  </FormItem>
                )}
              />
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
