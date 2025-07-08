import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { type StockDataResponse } from "@shared/schema";
import { Table as TableIcon, Download, Clock, TrendingUp, TrendingDown } from "lucide-react";

interface DataDisplayProps {
  data: StockDataResponse[];
  isLoading?: boolean;
}

export function DataDisplay({ data, isLoading }: DataDisplayProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);

  const handleDownload = () => {
    const csvContent = [
      ["종목코드", "종목명", "현재가", "전일대비", "등락률", "거래량", "시가총액"],
      ...data.map(item => [
        item.symbol,
        item.name,
        item.price?.toString() || "N/A",
        item.change?.toString() || "N/A",
        item.changePercent?.toString() || "N/A",
        item.volume?.toString() || "N/A",
        item.marketCap || "N/A"
      ])
    ].map(row => row.join(",")).join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `stock_data_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

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
            <p className="text-slate-400 text-lg">데이터를 수집하는 중...</p>
            <p className="text-slate-500 text-sm mt-2">잠시만 기다려주세요</p>
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
            <TableIcon className="h-5 w-5 text-blue-500" />
            수집된 데이터
          </CardTitle>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Clock className="h-4 w-4" />
              <span>마지막 업데이트: {new Date().toLocaleString('ko-KR')}</span>
            </div>
            {data.length > 0 && (
              <Button
                size="sm"
                onClick={handleDownload}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                <Download className="h-4 w-4 mr-2" />
                다운로드
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
              <TableIcon className="h-8 w-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">데이터가 없습니다</h3>
            <p className="text-slate-400 text-center">위의 설정을 통해 데이터를 수집해보세요</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">종목코드</TableHead>
                    <TableHead className="text-slate-300">종목명</TableHead>
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
                    총 <span className="font-medium text-white">{data.length}</span>개 중{" "}
                    <span className="font-medium text-white">
                      {startIndex + 1}-{Math.min(endIndex, data.length)}
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
