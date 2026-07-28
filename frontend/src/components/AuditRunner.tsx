"use client";

import { useState } from "react";
import {
  AnomalyFlag,
  ApiError,
  AuditRun,
  FlagResolution,
  resolveFlag,
  runAudit,
} from "@/services/auditApi";

const RESOLUTION_OPTIONS: { value: Exclude<FlagResolution, "unreviewed">; label: string }[] = [
  { value: "confirmed_issue", label: "Confirmed issue" },
  { value: "false_positive", label: "False positive" },
  { value: "no_action_needed", label: "No action needed" },
];

export function AuditRunResults({
  run,
  onFlagResolved,
}: {
  run: AuditRun;
  onFlagResolved?: (flag: AnomalyFlag) => void;
}) {
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleResolve(
    flagId: string,
    resolution: Exclude<FlagResolution, "unreviewed">
  ) {
    setError(null);
    setResolvingId(flagId);
    try {
      const updated = await resolveFlag(flagId, resolution);
      onFlagResolved?.(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record resolution.");
    } finally {
      setResolvingId(null);
    }
  }

  if (run.status === "insufficient_data") {
    return (
      <p>
        Not enough posted activity yet ({run.entries_evaluated} entries evaluated) to run a
        meaningful audit for {run.start} to {run.end}.
      </p>
    );
  }

  return (
    <>
      <p>
        {run.start} to {run.end} — evaluated {run.entries_evaluated} entries,{" "}
        <strong>{run.entries_flagged} flagged</strong>.
      </p>
      {error && <p className="error">{error}</p>}
      {run.flags.length === 0 ? (
        <p className="success-text">No anomalies found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Debit</th>
              <th>Credit</th>
              <th>Amount</th>
              <th>Reasons</th>
              <th>Explanation</th>
              <th>Resolution</th>
            </tr>
          </thead>
          <tbody>
            {run.flags.map((flag) => (
              <tr key={flag.id}>
                <td>{flag.journal_entry.date}</td>
                <td>{flag.journal_entry.debit_account.name}</td>
                <td>{flag.journal_entry.credit_account.name}</td>
                <td>{flag.journal_entry.amount}</td>
                <td>{flag.reason_categories.join(", ")}</td>
                <td>{flag.explanation}</td>
                <td>
                  {flag.resolution === "unreviewed" ? (
                    <select
                      value=""
                      disabled={resolvingId === flag.id}
                      onChange={(e) =>
                        handleResolve(
                          flag.id,
                          e.target.value as Exclude<FlagResolution, "unreviewed">
                        )
                      }
                    >
                      <option value="" disabled>
                        Resolve…
                      </option>
                      {RESOLUTION_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    RESOLUTION_OPTIONS.find((opt) => opt.value === flag.resolution)?.label ??
                    flag.resolution
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

export default function AuditRunner() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [run, setRun] = useState<AuditRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleRun() {
    setError(null);
    setBusy(true);
    try {
      const result = await runAudit(start || undefined, end || undefined);
      setRun(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to run audit.");
    } finally {
      setBusy(false);
    }
  }

  function handleFlagResolved(updated: AnomalyFlag) {
    setRun((prev) =>
      prev
        ? {
            ...prev,
            flags: prev.flags.map((f) => (f.id === updated.id ? updated : f)),
          }
        : prev
    );
  }

  return (
    <div className="panel">
      <h2>Audit</h2>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", alignItems: "flex-end" }}>
        <div className="field">
          <label htmlFor="audit-start">Start</label>
          <input
            id="audit-start"
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="audit-end">End</label>
          <input id="audit-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={handleRun} disabled={busy}>
          {busy ? "Running…" : "Run Audit"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {run && <AuditRunResults run={run} onFlagResolved={handleFlagResolved} />}
    </div>
  );
}
