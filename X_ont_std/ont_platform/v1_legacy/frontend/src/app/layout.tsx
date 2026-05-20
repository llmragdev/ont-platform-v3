import "./globals.css";
import type { Metadata } from "next";
import { UserProvider } from "@/context/UserContext";

export const metadata: Metadata = {
  title: "Claude 통합 - 온톨로지 AI 업무 콘솔",
  description: "팔란티어 스타일 온톨로지 + RAG + 워크플로우 통합 학습 콘솔",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
