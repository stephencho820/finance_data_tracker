import { Card, CardContent } from "@/components/ui/card";
import { useQuery } from "@tanstack/react-query";
import { type QuickStatsResponse } from "@shared/schema";
import { Building2, TrendingUp, ArrowUpDown, Coins, ArrowUp, ArrowDown } from "lucide-react";

export function QuickStats() {
  const { data: stats } = useQuery<QuickStatsResponse>({
    queryKey: ["/api/quick-stats"],
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const statsData = [
    {
      title: "총 수집 종목",
      value: stats?.totalStocks.toLocaleString() || "0",
      icon: Building2,
      color: "text-blue-500",
      bgColor: "bg-blue-500",
      change: "+12.5%",
      changeType: "positive" as const,
      period: "지난주 대비",
    },
    {
      title: "평균 수익률",
      value: stats ? `${stats.averageReturn >= 0 ? '+' : ''}${stats.averageReturn.toFixed(2)}%` : "0%",
      icon: TrendingUp,
      color: stats && stats.averageReturn >= 0 ? "text-green-500" : "text-red-500",
      bgColor: stats && stats.averageReturn >= 0 ? "bg-green-500" : "bg-red-500",
      change: "+0.45%",
      changeType: "positive" as const,
      period: "어제 대비",
    },
    {
      title: "총 거래량",
      value: stats ? formatVolume(stats.totalVolume) : "0",
      icon: ArrowUpDown,
      color: "text-blue-500",
      bgColor: "bg-blue-500",
      change: "-3.2%",
      changeType: "negative" as const,
      period: "지난주 대비",
    },
    {
      title: "시가총액",
      value: stats?.marketCap || "0",
      icon: Coins,
      color: "text-blue-500",
      bgColor: "bg-blue-500",
      change: "+1.8%",
      changeType: "positive" as const,
      period: "지난달 대비",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {statsData.map((stat, index) => (
        <Card key={index} className="bg-slate-900 border-slate-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{stat.title}</p>
                <p className={`text-2xl font-bold ${stat.color === 'text-blue-500' ? 'text-white' : stat.color}`}>
                  {stat.value}
                </p>
              </div>
              <div className={`w-12 h-12 ${stat.bgColor} bg-opacity-20 rounded-full flex items-center justify-center`}>
                <stat.icon className={`${stat.color} text-xl`} />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              {stat.changeType === "positive" ? (
                <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={stat.changeType === "positive" ? "text-green-500" : "text-red-500"}>
                {stat.change}
              </span>
              <span className="text-slate-400 ml-1">{stat.period}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function formatVolume(volume: number): string {
  if (volume >= 1e9) {
    return `${(volume / 1e9).toFixed(1)}B`;
  } else if (volume >= 1e6) {
    return `${(volume / 1e6).toFixed(1)}M`;
  } else if (volume >= 1e3) {
    return `${(volume / 1e3).toFixed(1)}K`;
  }
  return volume.toString();
}
