"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  TaxRulesDocument,
  TaxRulesDocumentSummary,
  addDocument,
  deleteDocument,
  getDocument,
  listDocuments,
} from "@/services/taxApi";

export default function TaxDocumentLibrary() {
  const [documents, setDocuments] = useState<TaxRulesDocumentSummary[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [viewing, setViewing] = useState<TaxRulesDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function load() {
    listDocuments()
      .then((res) => setDocuments(res.items))
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load the reference library.")
      );
  }

  useEffect(load, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;
    setError(null);
    setBusy(true);
    try {
      await addDocument(title, content);
      setTitle("");
      setContent("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add the document.");
    } finally {
      setBusy(false);
    }
  }

  async function handleView(id: string) {
    setError(null);
    try {
      const document = await getDocument(id);
      setViewing(document);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load that document.");
    }
  }

  async function handleDelete(id: string) {
    setError(null);
    try {
      await deleteDocument(id);
      if (viewing?.id === id) setViewing(null);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to remove that document.");
    }
  }

  return (
    <div className="panel">
      <h2>Tax Rules Reference Library</h2>

      <form onSubmit={handleAdd}>
        <div className="field">
          <label htmlFor="doc-title">Title</label>
          <input
            id="doc-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Quarterly estimated tax thresholds"
          />
        </div>
        <div className="field">
          <label htmlFor="doc-content">Content</label>
          <textarea
            id="doc-content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={5}
            placeholder="Paste the reference text here…"
          />
        </div>
        <button className="btn-primary" type="submit" disabled={busy}>
          Add to Library
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <table style={{ marginTop: "1rem" }}>
        <thead>
          <tr>
            <th>Title</th>
            <th>Chunks</th>
            <th>Added</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.title}</td>
              <td>{doc.chunk_count}</td>
              <td>{doc.created_at}</td>
              <td>
                <button className="btn-secondary" onClick={() => handleView(doc.id)}>
                  View
                </button>{" "}
                <button className="btn-secondary" onClick={() => handleDelete(doc.id)}>
                  Remove
                </button>
              </td>
            </tr>
          ))}
          {documents.length === 0 && (
            <tr>
              <td colSpan={4}>No reference documents yet.</td>
            </tr>
          )}
        </tbody>
      </table>

      {viewing && (
        <div style={{ marginTop: "1rem" }}>
          <h3>{viewing.title}</h3>
          <p style={{ whiteSpace: "pre-wrap" }}>{viewing.content}</p>
        </div>
      )}
    </div>
  );
}
