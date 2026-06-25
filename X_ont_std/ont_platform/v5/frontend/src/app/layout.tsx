import type { Metadata } from "next";
import { PerformanceVitals } from "@/components/PerformanceVitals";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ontology AI Workbench",
  description: "온톨로지와 워크플로우를 함께 설계하고 실행하는 AI 업무 플랫폼",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <PerformanceVitals />
        {children}
      </body>
    </html>
  );
}
