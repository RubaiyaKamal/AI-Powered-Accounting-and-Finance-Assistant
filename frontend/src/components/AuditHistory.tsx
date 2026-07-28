"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  AuditRun,
  AuditRunSummary,
  getAuditRun,
  listAuditRuns,
} from "@/services/auditApi";
import { AuditRunResults } from "@/components/AuditRunner";

export default function AuditHistory() {
  const [runs, setRuns] = useState<AuditRunSummary[]>([]);
  const [opened, setOpened] = useState<AuditRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAuditRuns()
      .then((res) => setRuns(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load audit history.")
      );
  }, []);

  async function handleOpen(id: string) {
    setError(null);
    try {
      const run = await getAuditRun(id);
      setOpened(run);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load that audit run.");
    }
  }

  function handleFlagResolved(updated: AuditRun["flags"][number]) {
    setOpened((prev) =>
      prev
        ? { ...prev, flags: prev.flags.map((f) => (f.id === updated.id ? updated : f)) }
        : prev
    );
  }

  return (
    <div className="panel">
      <h2>Audit History</h2>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Run date</th>
            <th>Period</th>
            <th>Status</th>
            <th>Evaluated</th>
            <th>Flagged</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id}>
              <td>{run.created_at}</td>
              <td>
                {run.start} to {run.end}
              </td>
              <td>{run.status}</td>
              <td>{run.entries_evaluated}</td>
              <td>{run.entries_flagged}</td>
              <td>
                <button className="btn-secondary" onClick={() => handleOpen(run.id)}>
                  View
                </button>
              </td>
            </tr>
          ))}
          {runs.length === 0 && (
            <tr>
              <td colSpan={6}>No audit runs yet.</td>
            </tr>
          )}
        </tbody>
      </table>

      {opened && (
        <div style={{ marginTop: "1rem" }}>
          <AuditRunResults run={opened} onFlagResolved={handleFlagResolved} />
        </div>
      )}
    </div>
  );
}
