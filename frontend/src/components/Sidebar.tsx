"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/expenses", label: "Expenses" },
  { href: "/ledger", label: "Ledger" },
  { href: "/reconciliation", label: "Reconciliation" },
  { href: "/reports", label: "Reports" },
  { href: "/audit", label: "Audit" },
  { href: "/tax", label: "Tax" },
  { href: "/analysis", label: "Analysis" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="app-sidebar">
      <nav>
        {LINKS.map((link) => {
          const isActive = pathname === link.href || pathname?.startsWith(`${link.href}/`);
          return (
            <Link key={link.href} href={link.href} className={isActive ? "active" : undefined}>
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
