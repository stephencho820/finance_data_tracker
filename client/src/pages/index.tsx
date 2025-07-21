// client/pages/index.tsx
import Head from "next/head";
import { useState } from "react";
import { DataCollectionForm } from "@/components/data-collection-form";
import { type StockDataResponse } from "@shared/schema";

export default function HomePage() {
  const [collectedData, setCollectedData] = useState<StockDataResponse[]>([]);

  return (
    <>
      <Head>
        <title>SCP Trading Agent</title>
      </Head>
      <main className="min-h-screen bg-gray-950 text-white p-6">
        <h1 className="text-3xl font-bold mb-6">SCP Trading Agent</h1>
        <DataCollectionForm
          collectedData={collectedData}
          onDataCollected={setCollectedData}
          mode="collect"
        />

        {collectedData.length > 0 && (
          <div className="mt-6">
            <h2 className="text-2xl font-semibold mb-4">수집된 데이터</h2>
            <table className="table-auto w-full text-sm border border-gray-700">
              <thead className="bg-gray-800">
                <tr>
                  <th className="p-2 border border-gray-700">Ticker</th>
                  <th className="p-2 border border-gray-700">Open</th>
                  <th className="p-2 border border-gray-700">High</th>
                  <th className="p-2 border border-gray-700">Low</th>
                  <th className="p-2 border border-gray-700">Close</th>
                  <th className="p-2 border border-gray-700">Volume</th>
                  <th className="p-2 border border-gray-700">Market Cap</th>
                  <th className="p-2 border border-gray-700">Best K</th>
                </tr>
              </thead>
              <tbody>
                {collectedData.map((item) => (
                  <tr key={item.ticker}>
                    <td className="p-2 border border-gray-700">{item.ticker}</td>
                    <td className="p-2 border border-gray-700">{item.open_price}</td>
                    <td className="p-2 border border-gray-700">{item.high_price}</td>
                    <td className="p-2 border border-gray-700">{item.low_price}</td>
                    <td className="p-2 border border-gray-700">{item.close_price}</td>
                    <td className="p-2 border border-gray-700">{item.volume}</td>
                    <td className="p-2 border border-gray-700">{item.market_cap}</td>
                    <td className="p-2 border border-gray-700">{item.best_k ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
