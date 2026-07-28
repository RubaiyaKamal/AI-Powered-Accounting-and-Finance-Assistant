"use client";

import { useState } from "react";
import BankStatementImport from "@/components/BankStatementImport";
import ReconciliationQueue from "@/components/ReconciliationQueue";

export default function ReconciliationPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = () => setRefreshKey((k) => k + 1);

  return (
    <main>
      <BankStatementImport onImported={refresh} />
      <ReconciliationQueue refreshKey={refreshKey} />
    </main>
  );
}
