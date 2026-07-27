import type { Metadata } from "next";
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
        </header>
        {children}
      </body>
    </html>
  );
}
