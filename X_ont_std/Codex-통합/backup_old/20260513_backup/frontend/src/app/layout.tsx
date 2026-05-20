import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Codex Ontology Workbench",
  description: "Ontology-first AI workbench"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

