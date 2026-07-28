"use client";

import TaxDocumentLibrary from "@/components/TaxDocumentLibrary";
import TaxSummaryGenerator from "@/components/TaxSummaryGenerator";

export default function TaxPage() {
  return (
    <main>
      <TaxSummaryGenerator />
      <TaxDocumentLibrary />
    </main>
  );
}
