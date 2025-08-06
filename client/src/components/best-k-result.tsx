import React, { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  Award,
  AlertTriangle,
  Filter,
  RefreshCw,
  Download,
  Eye,
  EyeOff,
} from "lucide-react";

interface BestKResult {
  ticker: string;
  companyName: string;
  market: string;
  marketCap: number;
  closePrice: number;
  periodType: string;
  periodDays: number;
  bestK: number;
  avgReturnPct: number;
  winRatePct: number;
  mddPct: number;
  totalTrades: number;
  sharpeRatio: number;
  analysisDate: string;
  createdAt: string;
}

interface BestKStats {
  totalCount: number;
  avgReturn: number;
  avgWinRate: number;
  avgMdd: number;
  avgSharpe: number;
  maxReturn: number;
  minReturn: number;
}

const BestKResults: React.FC = () => {
  const [results, setResults] = useState<BestKResult[]>([]);
  const [stats, setStats] = useState<BestKStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // 필터 상태
  const [selectedPeriod, setSelectedPeriod] = useState("all");
  const [selectedMarket, setSelectedMarket] = useState("ALL");
  const [resultLimit, setResultLimit] = useState(50);
  const [showDetails, setShowDetails] = useState(false);

  const periods = [
    { value: "all", label: "전체 기간" },
    { value: "days_3", label: "3일" },
    { value: "week_1", label: "1주일" },
    { value: "month_1", label: "1개월" },
    { value: "month_3", label: "3개월" },
    { value: "half_year", label: "6개월" },
    { value: "year_1", label: "1년" },
  ];

  const markets = [
    { value: "ALL", label: "전체" },
    { value: "KOSPI", label: "KOSPI" },
    { value: "KOSDAQ", label: "KOSDAQ" },
  ];

  const fetchResults = async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        period: selectedPeriod,
        market: selectedMarket,
        limit: resultLimit.toString(),
      });

      const response = await fetch(`/api/best-k-results?${params}`);
      const data = await response.json();

      if (data.success) {
        setResults(data.data.results);
        setStats(data.data.stats);
      } else {
        setError(data.message || "데이터 조회 실패");
      }
    } catch (err) {
      setError("네트워크 오류가 발생했습니다");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [selectedPeriod, selectedMarket, resultLimit]);

  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals);
  };

  const formatMarketCap = (marketCap: number) => {
    if (marketCap >= 1e12) return `${(marketCap / 1e12).toFixed(1)}조`;
    if (marketCap >= 1e8) return `${(marketCap / 1e8).toFixed(0)}억`;
    return `${marketCap.toLocaleString()}원`;
  };

  const getReturnColor = (returnPct: number) => {
    if (returnPct >= 1) return "text-green-600 bg-green-50";
    if (returnPct >= 0.5) return "text-blue-600 bg-blue-50";
    if (returnPct >= 0) return "text-gray-600 bg-gray-50";
    return "text-red-600 bg-red-50";
  };

  const getSharpeColor = (sharpe: number) => {
    if (sharpe >= 0.5) return "text-purple-600 bg-purple-50";
    if (sharpe >= 0.2) return "text-blue-600 bg-blue-50";
    if (sharpe >= 0) return "text-gray-600 bg-gray-50";
    return "text-red-600 bg-red-50";
  };

  return (
    <div className="bg-slate-900 p-6 rounded-lg">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <BarChart3 className="text-blue-400" size={24} />
          <h2 className="text-xl font-bold text-white">Best K 계산 결과</h2>
          {stats && (
            <span className="text-sm text-slate-400">
              ({stats.totalCount}개 종목)
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm transition-colors"
          >
            {showDetails ? <EyeOff size={14} /> : <Eye size={14} />}
            <span>{showDetails ? "간단히" : "자세히"}</span>
          </button>

          <button
            onClick={fetchResults}
            disabled={loading}
            className="flex items-center space-x-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded text-sm transition-colors"
          >
            <RefreshCw
              className={`${loading ? "animate-spin" : ""}`}
              size={14}
            />
            <span>새로고침</span>
          </button>
        </div>
      </div>

      {/* 필터 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-slate-800 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            분석 기간
          </label>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:ring-2 focus:ring-blue-500"
          >
            {periods.map((period) => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            시장 구분
          </label>
          <select
            value={selectedMarket}
            onChange={(e) => setSelectedMarket(e.target.value)}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:ring-2 focus:ring-blue-500"
          >
            {markets.map((market) => (
              <option key={market.value} value={market.value}>
                {market.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            표시 개수
          </label>
          <select
            value={resultLimit}
            onChange={(e) => setResultLimit(parseInt(e.target.value))}
            className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:ring-2 focus:ring-blue-500"
          >
            <option value={20}>상위 20개</option>
            <option value={50}>상위 50개</option>
            <option value={100}>상위 100개</option>
            <option value={200}>전체</option>
          </select>
        </div>

        <div className="flex items-end">
          <div className="text-xs text-slate-400">Sharpe Ratio 기준 정렬</div>
        </div>
      </div>

      {/* 통계 요약 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <TrendingUp className="text-green-400" size={16} />
              <span className="text-xs text-slate-400">평균 수익률</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.avgReturn)}%
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <Target className="text-blue-400" size={16} />
              <span className="text-xs text-slate-400">평균 승률</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.avgWinRate)}%
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <TrendingDown className="text-red-400" size={16} />
              <span className="text-xs text-slate-400">평균 MDD</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.avgMdd)}%
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <Award className="text-purple-400" size={16} />
              <span className="text-xs text-slate-400">평균 Sharpe</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.avgSharpe)}
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <TrendingUp className="text-emerald-400" size={16} />
              <span className="text-xs text-slate-400">최고 수익률</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.maxReturn)}%
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-1">
              <AlertTriangle className="text-orange-400" size={16} />
              <span className="text-xs text-slate-400">최저 수익률</span>
            </div>
            <div className="text-lg font-bold text-white">
              {formatNumber(stats.minReturn)}%
            </div>
          </div>
        </div>
      )}

      {/* 에러 표시 */}
      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="animate-spin text-blue-400" size={24} />
          <span className="ml-2 text-slate-400">데이터 로딩 중...</span>
        </div>
      )}

      {/* 결과 테이블 */}
      {!loading && results.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-2 text-slate-300 font-medium">
                  순위
                </th>
                <th className="text-left py-3 px-2 text-slate-300 font-medium">
                  종목
                </th>
                <th className="text-left py-3 px-2 text-slate-300 font-medium">
                  시장
                </th>
                {showDetails && (
                  <th className="text-right py-3 px-2 text-slate-300 font-medium">
                    시총
                  </th>
                )}
                <th className="text-right py-3 px-2 text-slate-300 font-medium">
                  Best K
                </th>
                <th className="text-right py-3 px-2 text-slate-300 font-medium">
                  수익률
                </th>
                <th className="text-right py-3 px-2 text-slate-300 font-medium">
                  승률
                </th>
                <th className="text-right py-3 px-2 text-slate-300 font-medium">
                  MDD
                </th>
                <th className="text-right py-3 px-2 text-slate-300 font-medium">
                  Sharpe
                </th>
                {showDetails && (
                  <th className="text-right py-3 px-2 text-slate-300 font-medium">
                    거래횟수
                  </th>
                )}
                {showDetails && (
                  <th className="text-right py-3 px-2 text-slate-300 font-medium">
                    분석일수
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {results.map((result, index) => (
                <tr
                  key={`${result.ticker}-${result.periodType}`}
                  className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                >
                  <td className="py-3 px-2 text-slate-400">#{index + 1}</td>
                  <td className="py-3 px-2">
                    <div>
                      <div className="text-white font-medium">
                        {result.companyName}
                      </div>
                      <div className="text-slate-400 text-xs">
                        {result.ticker}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        result.market === "KOSPI"
                          ? "bg-blue-500/20 text-blue-400"
                          : "bg-green-500/20 text-green-400"
                      }`}
                    >
                      {result.market}
                    </span>
                  </td>
                  {showDetails && (
                    <td className="py-3 px-2 text-right text-slate-300">
                      {formatMarketCap(result.marketCap)}
                    </td>
                  )}
                  <td className="py-3 px-2 text-right">
                    <span className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs font-bold">
                      {formatNumber(result.bestK, 1)}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right">
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${getReturnColor(result.avgReturnPct)}`}
                    >
                      {formatNumber(result.avgReturnPct)}%
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right text-slate-300">
                    {formatNumber(result.winRatePct)}%
                  </td>
                  <td className="py-3 px-2 text-right text-slate-300">
                    {formatNumber(result.mddPct)}%
                  </td>
                  <td className="py-3 px-2 text-right">
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${getSharpeColor(result.sharpeRatio)}`}
                    >
                      {formatNumber(result.sharpeRatio)}
                    </span>
                  </td>
                  {showDetails && (
                    <td className="py-3 px-2 text-right text-slate-400 text-xs">
                      {result.totalTrades}회
                    </td>
                  )}
                  {showDetails && (
                    <td className="py-3 px-2 text-right text-slate-400 text-xs">
                      {result.periodDays}일
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 데이터 없음 */}
      {!loading && results.length === 0 && !error && (
        <div className="text-center py-8 text-slate-400">
          아직 Best K 계산 결과가 없습니다.
          <br />
          먼저 Best K 계산을 실행해주세요.
        </div>
      )}
    </div>
  );
};

export default BestKResults;
