"use client";

import { useState } from "react";
import IncomeForm from "@/components/IncomeForm";
import IncomeList from "@/components/IncomeList";

export default function IncomePage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = () => setRefreshKey((k) => k + 1);

  return (
    <main>
      <IncomeForm onCreated={refresh} />
      <IncomeList refreshKey={refreshKey} />
    </main>
  );
}
