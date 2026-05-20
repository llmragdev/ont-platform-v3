import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ontology AI Workbench",
  description: "지능형 객체 기반 의사결정 지원 시스템",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
