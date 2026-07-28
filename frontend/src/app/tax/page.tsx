"use client";

import TaxDocumentLibrary from "@/components/TaxDocumentLibrary";
import TaxSummaryGenerator from "@/components/TaxSummaryGenerator";
import TaxSummaryHistory from "@/components/TaxSummaryHistory";

export default function TaxPage() {
  return (
    <main>
      <TaxSummaryGenerator />
      <TaxSummaryHistory />
      <TaxDocumentLibrary />
    </main>
  );
}
