import asyncio
import time
from typing import List, Dict


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.last_run_summary = {}

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()

        # 1. Gọi Agent
        response = await self.agent.query(test_case["question"])
        latency = time.perf_counter() - start_time

        # 2. Chạy RAGAS metrics
        ragas_scores = await self.evaluator.score(test_case, response)

        # 3. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"],
            response["answer"],
            test_case["expected_answer"]
        )

        agent_metadata = response.get("metadata", {})
        agent_tokens = agent_metadata.get("tokens_used", 0)
        judge_tokens = judge_result.get("tokens_used", 0)
        total_tokens = agent_tokens + judge_tokens

        # Ưu tiên lấy cost trực tiếp từ metadata nếu có.
        agent_cost = agent_metadata.get("cost_usd", 0.0)
        judge_cost = judge_result.get("cost_usd", 0.0)

        return {
            "test_case": test_case["question"],
            "agent_response": response["answer"],
            "latency": latency,
            "ragas": ragas_scores,
            "judge": judge_result,
            "token_usage": {
                "agent_tokens": agent_tokens,
                "judge_tokens": judge_tokens,
                "total_tokens": total_tokens,
            },
            "cost_usage": {
                "agent_cost_usd": agent_cost,
                "judge_cost_usd": judge_cost,
                "total_cost_usd": agent_cost + judge_cost,
            },
            "status": "fail" if judge_result["final_score"] < 3 else "pass",
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        """
        run_started_at = time.perf_counter()
        results = []

        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i + batch_size]
            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        elapsed = time.perf_counter() - run_started_at
        self.last_run_summary = self.get_performance_report(results, elapsed)
        return results

    @staticmethod
    def _percentile(values: List[float], percentile: float) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]

        sorted_values = sorted(values)
        rank = (len(sorted_values) - 1) * percentile
        low = int(rank)
        high = min(low + 1, len(sorted_values) - 1)
        weight = rank - low
        return sorted_values[low] * (1 - weight) + sorted_values[high] * weight

    def get_performance_report(self, results: List[Dict], total_time_sec: float | None = None) -> Dict:
        """
        Tổng hợp báo cáo hiệu năng cho 1 lần benchmark:
        - latency stats: min, avg, p50, p95, max
        - throughput: tests/second
        - token/cost usage tổng
        """
        total_cases = len(results)
        latencies = [float(r.get("latency", 0.0)) for r in results]

        if total_time_sec is None:
            total_time_sec = sum(latencies)

        total_tokens = sum(r.get("token_usage", {}).get("total_tokens", 0) for r in results)
        total_cost_usd = sum(r.get("cost_usage", {}).get("total_cost_usd", 0.0) for r in results)

        pass_count = sum(1 for r in results if r.get("status") == "pass")
        fail_count = total_cases - pass_count

        return {
            "total_cases": total_cases,
            "passed_cases": pass_count,
            "failed_cases": fail_count,
            "total_runtime_sec": round(total_time_sec, 4),
            "throughput_cases_per_sec": round(total_cases / total_time_sec, 4) if total_time_sec > 0 else 0.0,
            "latency": {
                "min_sec": round(min(latencies), 4) if latencies else 0.0,
                "avg_sec": round(sum(latencies) / total_cases, 4) if total_cases else 0.0,
                "p50_sec": round(self._percentile(latencies, 0.50), 4) if latencies else 0.0,
                "p95_sec": round(self._percentile(latencies, 0.95), 4) if latencies else 0.0,
                "max_sec": round(max(latencies), 4) if latencies else 0.0,
            },
            "token_usage": {
                "total_tokens": int(total_tokens),
                "avg_tokens_per_case": round(total_tokens / total_cases, 2) if total_cases else 0.0,
            },
            "cost_usage": {
                "total_cost_usd": round(total_cost_usd, 6),
                "avg_cost_usd_per_case": round(total_cost_usd / total_cases, 6) if total_cases else 0.0,
            },
        }
