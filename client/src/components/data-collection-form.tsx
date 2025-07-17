"use client";

import { useState } from "react";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Calendar } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";

import { type StockDataResponse } from "@shared/schema";

export interface DataCollectionFormProps {
  collectedData: StockDataResponse[];
  onDataCollected: (data: StockDataResponse[]) => void;
  mode: "collect" | "simulate";
}

const today = new Date();
const maxStartDate = new Date(today);
maxStartDate.setFullYear(today.getFullYear() - 1);
maxStartDate.setDate(maxStartDate.getDate() + 1);

const FormSchema = z.object({
  startDate: z.string(),
  endDate: z.string(),
  market: z.enum(["kospi", "kosdaq"]),
  sortBy: z.literal("market_cap"),
  rangeTop: z.coerce.number().min(1).max(199),
  rangeBottom: z.coerce.number().min(2).max(200),
});

export type FormData = z.infer<typeof FormSchema>;

export default function DataCollectionForm({
  collectedData,
  onDataCollected,
  mode,
}: DataCollectionFormProps) {
  const { toast } = useToast();

  const defaultDates = getDefaultDates();

  const form = useForm<FormData>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      startDate: defaultDates.startDate,
      endDate: defaultDates.endDate,
      market: "kospi",
      sortBy: "market_cap",
      rangeTop: 10,
      rangeBottom: 20,
    },
  });

  const handleCollectData = async () => {
    try {
      const formData = form.getValues();
      const response = await apiRequest("POST", "/api/collect-data", {
        startDate: formData.startDate,
        endDate: formData.endDate,
        market: formData.market,
      });
      const result = await response.json();
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
    } catch (error) {
      console.error(error);
      toast({
        title: "에러",
        description: "데이터 수집 중 오류가 발생했습니다.",
        variant: "destructive",
      });
    }
  };

  const handleBestK = async () => {
    try {
      const formData = form.getValues();
      const res = await apiRequest("GET", `/api/best-k/${formData.endDate}`);
      const bestKList = await res.json();
      if (bestKList.success === false) {
        toast({
          title: "Best K 계산 실패",
          description: bestKList.message,
          variant: "destructive",
        });
        return;
      }

      const updated = collectedData.map((item) => {
        const found = bestKList.find((b: any) => b.code === item.symbol);
        return found ? { ...item, best_k: found.best_k } : item;
      });

      onDataCollected(updated);
      toast({
        title: "Best K 계산 완료",
        description: `총 ${bestKList.length} 종목의 Best K가 업데이트 되었습니다.`,
      });
    } catch (e) {
      console.error(e);
      toast({
        title: "Best K 계산 실패",
        description: "오류가 발생했습니다.",
        variant: "destructive",
      });
    }
  };

  const handleSimulate = (values: FormData) => {
    if (values.rangeBottom <= values.rangeTop) {
      toast({
        title: "입력 오류",
        description: "Bottom은 Top보다 커야 합니다.",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "시뮬레이션 시작",
      description: JSON.stringify(values, null, 2),
    });

    // TODO: 여기에 시뮬레이션 API 호출 추가
  };

  return (
    <Card className="bg-slate-900 border-slate-700 p-6 space-y-4">
      {mode === "collect" && (
        <div className="flex gap-3">
          <Button
            onClick={handleCollectData}
            className="bg-blue-600 text-white hover:bg-blue-700"
          >
            데이터 수집
          </Button>
          <Button
            onClick={handleBestK}
            className="bg-green-600 text-white hover:bg-green-700"
          >
            Best K 산정
          </Button>
        </div>
      )}

      {mode === "simulate" && (
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSimulate)}
            className="space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 시작 날짜 */}
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
                          max={today.toISOString().split("T")[0]}
                          min={maxStartDate.toISOString().split("T")[0]}
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                        <Calendar className="absolute right-3 top-3 h-4 w-4 text-slate-400" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 종료 날짜 */}
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
                          max={today.toISOString().split("T")[0]}
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                        <Calendar className="absolute right-3 top-3 h-4 w-4 text-slate-400" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 시장 선택 */}
              <FormField
                control={form.control}
                name="market"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">시장 선택</FormLabel>
                    <Select
                      defaultValue={field.value}
                      onValueChange={field.onChange}
                    >
                      <FormControl>
                        <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="bg-slate-800 border-slate-600">
                        <SelectItem value="kospi" className="text-white">
                          KOSPI
                        </SelectItem>
                        <SelectItem value="kosdaq" className="text-white">
                          KOSDAQ
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* 정렬 기준 (비활성화) */}
              <FormField
                control={form.control}
                name="sortBy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">정렬 기준</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        disabled
                        value="market_cap"
                        className="bg-slate-800 border-slate-600 text-white"
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              {/* Range Top */}
              <FormField
                control={form.control}
                name="rangeTop"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">
                      시뮬레이션 Range Top
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        min={1}
                        max={199}
                        className="bg-slate-800 border-slate-600 text-white"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Range Bottom */}
              <FormField
                control={form.control}
                name="rangeBottom"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-slate-300">
                      시뮬레이션 Range Bottom
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        {...field}
                        min={2}
                        max={200}
                        className="bg-slate-800 border-slate-600 text-white"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                className="bg-yellow-600 text-white hover:bg-yellow-700"
              >
                시뮬레이션 시작
              </Button>
            </div>
          </form>
        </Form>
      )}
    </Card>
  );
}

function getDefaultDates() {
  const today = new Date();
  const endDate = new Date(today);
  endDate.setDate(today.getDate() - 1);

  const startDate = new Date(today);
  startDate.setDate(today.getDate() - 2);

  return {
    startDate: startDate.toISOString().split("T")[0],
    endDate: endDate.toISOString().split("T")[0],
  };
}
