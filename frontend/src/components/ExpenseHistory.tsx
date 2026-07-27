import { EditHistoryEntry } from "@/services/expensesApi";

export default function ExpenseHistory({ history }: { history: EditHistoryEntry[] }) {
  if (history.length === 0) {
    return <p style={{ fontSize: "0.85rem", color: "var(--color-secondary)" }}>No edits yet.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Field</th>
          <th>Old value</th>
          <th>New value</th>
          <th>Changed</th>
        </tr>
      </thead>
      <tbody>
        {history.map((h, i) => (
          <tr key={i}>
            <td>{h.field_name}</td>
            <td>{h.old_value ?? "—"}</td>
            <td>{h.new_value ?? "—"}</td>
            <td>{new Date(h.changed_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
