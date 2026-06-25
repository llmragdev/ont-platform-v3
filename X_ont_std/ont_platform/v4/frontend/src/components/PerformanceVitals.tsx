"use client";

import { useReportWebVitals } from "next/web-vitals";

const ENABLE_PERF_LOG = process.env.NEXT_PUBLIC_ENABLE_PERF_LOG === "true";

export function PerformanceVitals() {
  useReportWebVitals((metric) => {
    if (!ENABLE_PERF_LOG) return;
    console.info("[web-vitals]", metric.name, Math.round(metric.value), metric.rating);
  });

  return null;
}
