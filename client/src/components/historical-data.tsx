import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { type StockDataResponse } from "@shared/schema";
import { Database, RotateCcw, TrendingUp, TrendingDown } from "lucide-react";

export function HistoricalData() {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const { data, isLoading, refetch } = useQuery<{ success: boolean; data: StockDataResponse[]; total: number }>({
    queryKey: ["/api/stock-data"],
    refetchInterval: 60000, // Refetch every minute
  });

  const stockData = data?.data || [];
  const totalPages = Math.ceil(stockData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = stockData.slice(startIndex, endIndex);

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "N/A";
    return num.toLocaleString();
  };

  const formatPercent = (num: number | null | undefined) => {
    if (num === null || num === undefined) return "N/A";
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
  };

  const formatPrice = (price: number | null | undefined, country: string) => {
    if (price === null || price === undefined) return "N/A";
    if (country === "korea") {
      return `${formatNumber(price)}원`;
    } else {
      return `$${formatNumber(price)}`;
    }
  };

  const formatChange = (change: number | null | undefined, country: string) => {
    if (change === null || change === undefined) return "N/A";
    const symbol = change >= 0 ? '+' : '';
    if (country === "korea") {
      return `${symbol}${formatNumber(change)}원`;
    } else {
      return `${symbol}$${formatNumber(change)}`;
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-slate-900 border-slate-700">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <p className="text-slate-400 text-lg">데이터베이스에서 데이터를 불러오는 중...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-900 border-slate-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-white">
            <Database className="h-5 w-5 text-green-500" />
            저장된 데이터
          </CardTitle>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-600">
              총 {stockData.length}개 종목
            </Badge>
            <Button
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
              className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              새로고침
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {stockData.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
              <Database className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">저장된 데이터가 없습니다</h3>
            <p className="text-slate-400 text-center">데이터 수집을 통해 데이터를 저장해보세요</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">종목코드</TableHead>
                    <TableHead className="text-slate-300">종목명</TableHead>
                    <TableHead className="text-slate-300">시장</TableHead>
                    <TableHead className="text-slate-300 text-right">현재가</TableHead>
                    <TableHead className="text-slate-300 text-right">전일대비</TableHead>
                    <TableHead className="text-slate-300 text-right">등락률</TableHead>
                    <TableHead className="text-slate-300 text-right">거래량</TableHead>
                    <TableHead className="text-slate-300 text-right">시가총액</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentData.map((item, index) => (
                    <TableRow key={index} className="border-slate-700 hover:bg-slate-800">
                      <TableCell className="font-mono text-slate-300">{item.symbol}</TableCell>
                      <TableCell className="font-medium text-white">{item.name}</TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={`${
                            item.country === 'korea' 
                              ? 'bg-blue-500/20 text-blue-300 border-blue-500/50' 
                              : 'bg-purple-500/20 text-purple-300 border-purple-500/50'
                          }`}
                        >
                          {item.market}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right text-white">
                        {formatPrice(item.price, item.country)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={
                          item.change && item.change >= 0 ? "text-green-500" : "text-red-500"
                        }>
                          {formatChange(item.change, item.country)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          {item.changePercent && item.changePercent >= 0 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <span className={
                            item.changePercent && item.changePercent >= 0 ? "text-green-500" : "text-red-500"
                          }>
                            {formatPercent(item.changePercent)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {formatNumber(item.volume)}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {item.marketCap || "N/A"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-6 border-t border-slate-700">
                <div className="flex items-center text-sm text-slate-400">
                  <span>
                    총 <span className="font-medium text-white">{stockData.length}</span>개 중{" "}
                    <span className="font-medium text-white">
                      {startIndex + 1}-{Math.min(endIndex, stockData.length)}
                    </span>개 표시
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    이전
                  </Button>
                  <span className="text-sm text-slate-400">
                    {currentPage} / {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    다음
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}