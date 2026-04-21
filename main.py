import asyncio
import json
import os
import time
from typing import Dict, List, Any

from engine.runner import BenchmarkRunner
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge
from agent.main_agent import MainAgent


# ================================================================
# RELEASE GATE LOGIC - Nguoi 6 (Pham Viet Hoang)
# ================================================================

def release_decision(
    v1_summary: Dict[str, Any],
    v2_summary: Dict[str, Any],
    thresholds: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Quyet dinh co release phien ban V2 hay khong dua tren Delta Analysis.

    Tieu chi Release Gate:
    1. Chat luong (Quality): avg_score V2 >= V1 + min_delta_score
    2. Retrieval: hit_rate V2 >= hit_rate V1 - max_hit_rate_regression
    3. Dong thuan: agreement_rate V2 >= min_agreement
    4. Hieu nang: latency V2 <= latency V1 * max_latency_ratio
    5. Chi phi: cost V2 <= cost V1 * max_cost_ratio

    Tra ve dict chua quyet dinh va ly do chi tiet.
    """
    if thresholds is None:
        thresholds = {
            "min_delta_score": 0.0,          # V2 phai cao hon V1 it nhat 0 diem
            "max_hit_rate_regression": 0.05,  # Cho phep hit_rate giam toi da 5%
            "min_agreement": 0.7,             # Agreement rate toi thieu 70%
            "max_latency_ratio": 1.2,         # Latency V2 <= 120% V1
            "max_cost_ratio": 1.15,           # Cost V2 <= 115% V1
        }

    v1_metrics = v1_summary.get("metrics", {})
    v2_metrics = v2_summary.get("metrics", {})

    # Tinh delta
    delta_score = v2_metrics.get("avg_score", 0) - v1_metrics.get("avg_score", 0)
    delta_hit_rate = v2_metrics.get("hit_rate", 0) - v1_metrics.get("hit_rate", 0)
    delta_agreement = v2_metrics.get("agreement_rate", 0) - v1_metrics.get("agreement_rate", 0)

    # Latency & Cost (neu co)
    v1_latency = v1_metrics.get("avg_latency", 0)
    v2_latency = v2_metrics.get("avg_latency", 0)
    latency_ratio = v2_latency / v1_latency if v1_latency > 0 else 0

    v1_cost = v1_metrics.get("avg_cost", 0)
    v2_cost = v2_metrics.get("avg_cost", 0)
    cost_ratio = v2_cost / v1_cost if v1_cost > 0 else 0

    # Kiem tra tung tieu chi
    checks = {
        "quality_delta": {
            "pass": delta_score >= thresholds["min_delta_score"],
            "value": delta_score,
            "threshold": thresholds["min_delta_score"],
            "message": f"Delta Score: {'+' if delta_score >= 0 else ''}{delta_score:.3f} (threshold: >= {thresholds['min_delta_score']})"
        },
        "hit_rate": {
            "pass": delta_hit_rate >= -thresholds["max_hit_rate_regression"],
            "value": delta_hit_rate,
            "threshold": -thresholds["max_hit_rate_regression"],
            "message": f"Delta Hit Rate: {'+' if delta_hit_rate >= 0 else ''}{delta_hit_rate:.3f} (threshold: >= {-thresholds['max_hit_rate_regression']})"
        },
        "agreement": {
            "pass": v2_metrics.get("agreement_rate", 0) >= thresholds["min_agreement"],
            "value": v2_metrics.get("agreement_rate", 0),
            "threshold": thresholds["min_agreement"],
            "message": f"V2 Agreement Rate: {v2_metrics.get('agreement_rate', 0):.3f} (threshold: >= {thresholds['min_agreement']})"
        },
        "latency": {
            "pass": latency_ratio <= thresholds["max_latency_ratio"] or v1_latency == 0,
            "value": latency_ratio,
            "threshold": thresholds["max_latency_ratio"],
            "message": f"Latency Ratio: {latency_ratio:.3f}x (threshold: <= {thresholds['max_latency_ratio']}x)"
        },
        "cost": {
            "pass": cost_ratio <= thresholds["max_cost_ratio"] or v1_cost == 0,
            "value": cost_ratio,
            "threshold": thresholds["max_cost_ratio"],
            "message": f"Cost Ratio: {cost_ratio:.3f}x (threshold: <= {thresholds['max_cost_ratio']}x)"
        }
    }

    # Quyet dinh tong the
    all_pass = all(c["pass"] for c in checks.values())
    failed_checks = [name for name, c in checks.items() if not c["pass"]]

    decision = {
        "approve": all_pass,
        "version": "V2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "thresholds": thresholds,
        "checks": checks,
        "failed_checks": failed_checks,
        "summary": {
            "v1_avg_score": v1_metrics.get("avg_score", 0),
            "v2_avg_score": v2_metrics.get("avg_score", 0),
            "delta_score": delta_score,
            "v1_hit_rate": v1_metrics.get("hit_rate", 0),
            "v2_hit_rate": v2_metrics.get("hit_rate", 0),
            "v1_agreement": v1_metrics.get("agreement_rate", 0),
            "v2_agreement": v2_metrics.get("agreement_rate", 0),
        }
    }

    if all_pass:
        decision["message"] = "RELEASE APPROVED: V2 dat tat ca tieu chi Release Gate."
    else:
        decision["message"] = f"RELEASE BLOCKED: V2 khong dat tieu chi {', '.join(failed_checks)}."

    return decision


# ================================================================
# BENCHMARK RUNNER
# ================================================================

async def run_benchmark_with_results(agent_version: str):
    print(f"Khoi dong Benchmark cho Agent {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("Thieu data/golden_set.jsonl. Hay chay 'python data/synthetic_gen.py' truoc.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("File data/golden_set.jsonl rong. Hay tao it nhat 1 test case.")
        return None, None

    agent = MainAgent(version=agent_version)
    evaluator = RetrievalEvaluator()
    judge = LLMJudge(simulation_mode=True)  # Dung simulation mode de khong can API key
    runner = BenchmarkRunner(agent, evaluator, judge)
    results = await runner.run_all(dataset)

    total = len(results)
    if total == 0:
        print("Khong co ket qua nao.")
        return None, None

    # Tinh metrics tong hop
    summary = {
        "metadata": {
            "version": agent_version,
            "total": total,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total,
            "avg_latency": sum(r["latency"] for r in results) / total,
            "pass_rate": sum(1 for r in results if r["status"] == "pass") / total,
        }
    }

    return results, summary


async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary


# ================================================================
# MAIN ENTRY POINT
# ================================================================

async def main():
    print("=" * 60)
    print("AI Evaluation Factory - Regression Benchmark")
    print("=" * 60)

    # Chay benchmark V1
    v1_results, v1_summary = await run_benchmark_with_results("v1")
    if not v1_summary:
        print("Khong the chay Benchmark V1. Kiem tra lai data/golden_set.jsonl.")
        return

    # Chay benchmark V2
    v2_results, v2_summary = await run_benchmark_with_results("v2")
    if not v2_summary:
        print("Khong the chay Benchmark V2. Kiem tra lai data/golden_set.jsonl.")
        return

    # -- Hien thi ket qua so sanh --
    print("\n" + "=" * 60)
    print("KET QUA SO SANH REGRESSION (V1 vs V2)")
    print("=" * 60)

    m1 = v1_summary["metrics"]
    m2 = v2_summary["metrics"]

    print(f"\n{'Metric':<25} {'V1':>12} {'V2':>12} {'Delta':>12}")
    print("-" * 65)
    print(f"{'Avg Score':<25} {m1['avg_score']:>12.3f} {m2['avg_score']:>12.3f} {'+' if m2['avg_score'] >= m1['avg_score'] else ''}{m2['avg_score'] - m1['avg_score']:>11.3f}")
    print(f"{'Hit Rate':<25} {m1['hit_rate']:>12.3f} {m2['hit_rate']:>12.3f} {'+' if m2['hit_rate'] >= m1['hit_rate'] else ''}{m2['hit_rate'] - m1['hit_rate']:>11.3f}")
    print(f"{'Agreement Rate':<25} {m1['agreement_rate']:>12.3f} {m2['agreement_rate']:>12.3f} {'+' if m2['agreement_rate'] >= m1['agreement_rate'] else ''}{m2['agreement_rate'] - m1['agreement_rate']:>11.3f}")
    print(f"{'Avg Latency (s)':<25} {m1['avg_latency']:>12.3f} {m2['avg_latency']:>12.3f} {'+' if m2['avg_latency'] >= m1['avg_latency'] else ''}{m2['avg_latency'] - m1['avg_latency']:>11.3f}")
    print(f"{'Pass Rate':<25} {m1['pass_rate']:>12.3f} {m2['pass_rate']:>12.3f} {'+' if m2['pass_rate'] >= m1['pass_rate'] else ''}{m2['pass_rate'] - m1['pass_rate']:>11.3f}")

    # -- Release Gate Decision --
    print("\n" + "=" * 60)
    print("RELEASE GATE DECISION")
    print("=" * 60)

    decision = release_decision(v1_summary, v2_summary)
    print(f"\n{decision['message']}\n")

    for check_name, check in decision["checks"].items():
        icon = "PASS" if check["pass"] else "FAIL"
        print(f"  [{icon}] {check['message']}")

    # -- Xuat reports --
    os.makedirs("reports", exist_ok=True)

    # Summary report (V2 la phien ban moi nhat)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)

    # Benchmark results chi tiet (V2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    # Regression report (so sanh V1 vs V2 + Release Gate)
    regression_report = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": v1_summary["metadata"]["total"]
        },
        "v1_summary": v1_summary,
        "v2_summary": v2_summary,
        "release_gate": decision
    }
    with open("reports/regression_report.json", "w", encoding="utf-8") as f:
        json.dump(regression_report, f, ensure_ascii=False, indent=2)

    print(f"\nDa luu reports:")
    print(f"   - reports/summary.json")
    print(f"   - reports/benchmark_results.json")
    print(f"   - reports/regression_report.json")


if __name__ == "__main__":
    asyncio.run(main())
