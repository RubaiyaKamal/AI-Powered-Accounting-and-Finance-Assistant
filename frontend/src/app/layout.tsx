import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI-Powered Accounting Assistant",
  description: "Manage expenses, income, and reports with an AI assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <header className="app-header">
          <h1>
            AI-Powered <span className="accent">Accounting</span> Assistant
          </h1>
          <nav style={{ marginTop: "0.5rem" }}>
            <Link href="/expenses" style={{ color: "inherit", marginRight: "1rem" }}>
              Expenses
            </Link>
            <Link href="/ledger" style={{ color: "inherit" }}>
              Ledger
            </Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
