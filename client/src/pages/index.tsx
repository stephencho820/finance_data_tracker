// 📄 client/src/pages/index.tsx
import Head from "next/head";
import { useState } from "react";

import DataCollectionForm from "@/components/data-collection-form";
import MarketCapSection from "@/components/market-cap-section";
import type { MarketCapRow } from "@/components/market-cap-table";

export default function HomePage() {
  const [collectedData, setCollectedData] = useState<MarketCapRow[]>([]);

  return (
    <>
      <Head>
        <title>SCP Trading Agent</title>
      </Head>
      <main className="min-h-screen bg-gray-950 text-white p-6 space-y-6">
        <h1 className="text-3xl font-bold">SCP Trading Agent</h1>

        <DataCollectionForm
          mode="collect"
          collectedData={collectedData}
          onDataCollected={setCollectedData}
        />

        {collectedData.length > 0 && <MarketCapSection data={collectedData} />}
      </main>
    </>
  );
}
