"use client";

import SpendingBreakdown from "@/components/SpendingBreakdown";
import SpendingForecast from "@/components/SpendingForecast";
import SpendingQuery from "@/components/SpendingQuery";

export default function AnalysisPage() {
  return (
    <main>
      <SpendingQuery />
      <SpendingBreakdown />
      <SpendingForecast />
    </main>
  );
}
