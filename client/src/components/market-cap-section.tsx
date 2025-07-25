"use client";

import { formatKoreanWon } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table as TableIcon } from "lucide-react";
import { useState, useEffect } from "react";

export interface MarketCapRow {
  name: string;
  date: string;
  ticker: string;
  market: "KOSPI" | "KOSDAQ";
  market_cap: number | null;
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  close_price: number | null;
  volume: number | null;
}

interface MarketCapSectionProps {
  data: MarketCapRow[];
}

const MarketCapSection = ({ data }: MarketCapSectionProps) => {
  const [selectedMarket, setSelectedMarket] = useState<"KOSPI" | "KOSDAQ">(
    "KOSPI",
  );
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const filtered = data.filter(
    (item) => item.market?.toUpperCase() === selectedMarket,
  );

  const sortedData = [...filtered].sort(
    (a, b) => (b.market_cap || 0) - (a.market_cap || 0),
  );

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentData = sortedData.slice(startIndex, startIndex + itemsPerPage);

  useEffect(() => {
    setCurrentPage(1); // 필터 변경 시 페이지 초기화
  }, [selectedMarket]);

  const format = (value: number | null | undefined) =>
    value != null ? value.toLocaleString() : "N/A";

  return (
    <Card className="bg-slate-900 border-slate-700">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <TableIcon className="h-5 w-5 text-blue-500" />
          Top 200 Market Cap
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* 🔘 Market 필터 버튼 */}
        <div className="flex items-center gap-2 mb-4">
          <Button
            className="flex-1"
            variant={selectedMarket === "KOSPI" ? "default" : "outline"}
            onClick={() => setSelectedMarket("KOSPI")}
          >
            KOSPI
          </Button>
          <Button
            className="flex-1"
            variant={selectedMarket === "KOSDAQ" ? "default" : "outline"}
            onClick={() => setSelectedMarket("KOSDAQ")}
          >
            KOSDAQ
          </Button>
        </div>

        {/* 📊 테이블 */}
        {sortedData.length === 0 ? (
          <p className="text-slate-400">데이터가 없습니다</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-300">종목명</TableHead>
                    <TableHead className="text-slate-300 text-right">
                      종목코드
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      시가
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      고가
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      저가
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      종가
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      거래량
                    </TableHead>
                    <TableHead className="text-slate-300 text-right">
                      시가총액
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {currentData.map((row) => (
                    <TableRow
                      key={row.ticker}
                      className="border-slate-700 hover:bg-slate-800"
                    >
                      <TableCell className="text-slate-300 font-semibold">
                        {row.name}
                      </TableCell>
                      <TableCell className="font-mono text-right text-slate-300">
                        {row.ticker}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {formatKoreanWon(row.open_price)}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {formatKoreanWon(row.high_price)}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {formatKoreanWon(row.low_price)}
                      </TableCell>
                      <TableCell className="text-right text-white font-medium">
                        {formatKoreanWon(row.close_price)}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {format(row.volume)}
                      </TableCell>
                      <TableCell className="text-right text-slate-300">
                        {formatKoreanWon(row.market_cap)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* 🔢 Pagination */}
            <div className="flex items-center justify-between mt-6 pt-6 border-t border-slate-700">
              <div className="text-sm text-slate-400">
                총{" "}
                <span className="text-white font-semibold">
                  {sortedData.length}
                </span>
                개 중{" "}
                <span className="text-white font-semibold">
                  {startIndex + 1}-
                  {Math.min(startIndex + itemsPerPage, sortedData.length)}
                </span>{" "}
                개 표시
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(1, prev - 1))
                  }
                  disabled={currentPage === 1}
                  className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  이전
                </Button>
                <span className="text-sm text-slate-400">
                  {currentPage} / {totalPages}
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  다음
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default MarketCapSection;
