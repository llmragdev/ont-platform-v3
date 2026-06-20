import numpy as np
from typing import Dict, List

class PerformanceEvaluator:
    def analyze(self, results: List[Dict]) -> Dict:
        """응답 시간 및 성공률을 분석합니다."""
        response_times = []
        success_count = 0
        total_queries = len(results)

        for item in results:
            # 성공 여부 확인
            status = item.get("status")
            if status in ["success", "ok"] or ("data" in item and item["data"] is not None):
                success_count += 1
            
            # 응답 시간(ms) 확인
            # debug_info 내 execution_time_ms 혹은 direct elapsed_ms 활용
            elapsed = item.get("elapsed_ms")
            if elapsed is None:
                debug_info = item.get("data", {}).get("debug_info") if item.get("data") else None
                if debug_info:
                    elapsed = debug_info.get("execution_time_ms")
            
            if elapsed is not None:
                response_times.append(float(elapsed))

        success_rate = (success_count / total_queries) if total_queries > 0 else 0.0

        if not response_times:
            return {
                "success_rate": round(success_rate, 4),
                "avg_response_time_ms": 0.0,
                "p50_response_time_ms": 0.0,
                "p95_response_time_ms": 0.0,
                "p99_response_time_ms": 0.0,
                "min_response_time_ms": 0.0,
                "max_response_time_ms": 0.0
            }

        times_arr = np.array(response_times)
        
        return {
            "success_rate": round(success_rate, 4),
            "avg_response_time_ms": round(float(np.mean(times_arr)), 2),
            "p50_response_time_ms": round(float(np.percentile(times_arr, 50)), 2),
            "p95_response_time_ms": round(float(np.percentile(times_arr, 95)), 2),
            "p99_response_time_ms": round(float(np.percentile(times_arr, 99)), 2),
            "min_response_time_ms": round(float(np.min(times_arr)), 2),
            "max_response_time_ms": round(float(np.max(times_arr)), 2)
        }
