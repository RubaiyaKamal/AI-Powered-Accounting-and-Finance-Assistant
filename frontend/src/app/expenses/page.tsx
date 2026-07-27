"use client";

import { useState } from "react";
import ExpenseForm from "@/components/ExpenseForm";
import ExpenseList from "@/components/ExpenseList";
import AssistantChat from "@/components/AssistantChat";

export default function ExpensesPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const refresh = () => setRefreshKey((k) => k + 1);

  return (
    <main>
      <AssistantChat onCreated={refresh} />
      <ExpenseForm onCreated={refresh} />
      <ExpenseList refreshKey={refreshKey} />
    </main>
  );
}
