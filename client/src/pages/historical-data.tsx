import React from 'react';
import { HistoricalDataViewer } from '../components/historical-data-viewer';

export function HistoricalData() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">역사적 주식 데이터</h1>
        <p className="text-gray-600">
          PostgreSQL 데이터베이스에 저장된 5년치 주식 데이터를 조회하고 분석할 수 있습니다.
        </p>
      </div>
      
      <HistoricalDataViewer />
    </div>
  );
}