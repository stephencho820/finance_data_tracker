import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Calendar, TrendingUp, BarChart3, DollarSign } from 'lucide-react';

interface HistoricalStock {
  id: number;
  date: string;
  symbol: string;
  name: string;
  market: string;
  rank_type: string;
  rank: number;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  market_cap: string;
  best_k_value?: number;
}

export function HistoricalDataViewer() {
  const [selectedDate, setSelectedDate] = useState<string>('2024-07-08');
  const [selectedMarket, setSelectedMarket] = useState<string>('all');
  const [selectedRankType, setSelectedRankType] = useState<string>('all');

  const { data: historicalData, isLoading, error } = useQuery<HistoricalStock[]>({
    queryKey: ['/api/daily-stock-data', selectedDate, selectedMarket, selectedRankType],
    queryFn: async () => {
      const params = new URLSearchParams({
        date: selectedDate,
        ...(selectedMarket !== 'all' && { market: selectedMarket }),
        ...(selectedRankType !== 'all' && { rank_type: selectedRankType })
      });
      const response = await fetch(`/api/daily-stock-data?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }
      return response.json();
    },
  });

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0
    }).format(price);
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toString();
  };

  const formatMarketCap = (marketCap: string) => {
    const value = parseFloat(marketCap);
    if (value >= 1000000000000) {
      return `${(value / 1000000000000).toFixed(1)}조`;
    } else if (value >= 100000000) {
      return `${(value / 100000000).toFixed(1)}억`;
    }
    return marketCap;
  };

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return 'bg-yellow-500';
    if (rank === 2) return 'bg-gray-400';
    if (rank === 3) return 'bg-amber-600';
    if (rank <= 10) return 'bg-blue-500';
    return 'bg-gray-500';
  };

  const groupedData = historicalData?.reduce((acc, item) => {
    const key = `${item.market}-${item.rank_type}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(item);
    return acc;
  }, {} as Record<string, HistoricalStock[]>);

  if (isLoading) return <div className="p-4">역사적 데이터를 불러오는 중...</div>;
  if (error) return <div className="p-4 text-red-500">데이터를 불러오는 중 오류가 발생했습니다.</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            역사적 주식 데이터
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2">
              <label htmlFor="date" className="text-sm font-medium">날짜:</label>
              <Input
                id="date"
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="market" className="text-sm font-medium">시장:</label>
              <Select value={selectedMarket} onValueChange={setSelectedMarket}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="KOSPI">KOSPI</SelectItem>
                  <SelectItem value="KOSDAQ">KOSDAQ</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="rank-type" className="text-sm font-medium">랭킹 유형:</label>
              <Select value={selectedRankType} onValueChange={setSelectedRankType}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="market_cap">시가총액</SelectItem>
                  <SelectItem value="volume">거래량</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {groupedData && Object.keys(groupedData).length > 0 ? (
            <Tabs defaultValue={Object.keys(groupedData)[0]} className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                {Object.keys(groupedData).map((key) => {
                  const [market, rankType] = key.split('-');
                  return (
                    <TabsTrigger key={key} value={key} className="text-xs">
                      {market} {rankType === 'market_cap' ? '시가총액' : '거래량'}
                    </TabsTrigger>
                  );
                })}
              </TabsList>

              {Object.entries(groupedData).map(([key, stocks]) => (
                <TabsContent key={key} value={key} className="space-y-4">
                  <div className="grid gap-4">
                    {stocks.sort((a, b) => a.rank - b.rank).map((stock) => (
                      <Card key={`${stock.symbol}-${stock.rank_type}`} className="border-l-4 border-l-blue-500">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                              <Badge className={`${getRankBadgeColor(stock.rank)} text-white`}>
                                {stock.rank}위
                              </Badge>
                              <div>
                                <h3 className="font-semibold">{stock.name}</h3>
                                <p className="text-sm text-gray-600">{stock.symbol}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold">{formatPrice(stock.close_price)}</p>
                              <p className="text-sm text-gray-500">{stock.market}</p>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                            <div className="flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-blue-500" />
                              <div>
                                <p className="text-xs text-gray-500">시가</p>
                                <p className="font-medium">{formatPrice(stock.open_price)}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-green-500" />
                              <div>
                                <p className="text-xs text-gray-500">고가</p>
                                <p className="font-medium">{formatPrice(stock.high_price)}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-red-500" />
                              <div>
                                <p className="text-xs text-gray-500">저가</p>
                                <p className="font-medium">{formatPrice(stock.low_price)}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <BarChart3 className="w-4 h-4 text-purple-500" />
                              <div>
                                <p className="text-xs text-gray-500">거래량</p>
                                <p className="font-medium">{formatVolume(stock.volume)}</p>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between mt-4 pt-4 border-t">
                            <div className="flex items-center gap-2">
                              <DollarSign className="w-4 h-4 text-green-600" />
                              <div>
                                <p className="text-xs text-gray-500">시가총액</p>
                                <p className="font-medium">{formatMarketCap(stock.market_cap)}</p>
                              </div>
                            </div>
                            {stock.best_k_value && (
                              <div>
                                <p className="text-xs text-gray-500">Best K 값</p>
                                <Badge variant="outline">{stock.best_k_value.toFixed(4)}</Badge>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">선택한 날짜에 데이터가 없습니다.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}