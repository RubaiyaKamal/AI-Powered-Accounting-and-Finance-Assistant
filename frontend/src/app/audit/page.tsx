"use client";

import AuditHistory from "@/components/AuditHistory";
import AuditRunner from "@/components/AuditRunner";

export default function AuditPage() {
  return (
    <main>
      <AuditRunner />
      <AuditHistory />
    </main>
  );
}
