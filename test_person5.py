"""
test_person5.py — Test toàn bộ công việc của Người 5 (Phạm Đình Trường)
Chạy: python test_person5.py
"""
import asyncio
import sys

sys.path.insert(0, ".")

from engine.retrieval_eval import RetrievalEvaluator
from agent.main_agent import MainAgent

PASS = "[PASS]"
FAIL = "[FAIL]"


def check(label, actual, expected, tol=0.01):
    ok = abs(actual - expected) <= tol
    icon = PASS if ok else FAIL
    print(f"  {icon}  {label}: got={actual}, expected={expected}")
    return ok


async def test_retrieval_eval():
    print("=" * 55)
    print("  KIEM TRA engine/retrieval_eval.py")
    print("=" * 55)
    ev = RetrievalEvaluator()
    results = []

    # ── Hit Rate ──────────────────────────────────────────
    print("\n[1] calculate_hit_rate")
    results.append(check("hit=1 khi co doc dung trong top3",
        ev.calculate_hit_rate(["doc_001","doc_002"], ["doc_003","doc_001","doc_005"], top_k=3), 1.0))
    results.append(check("hit=0 khi khong co doc dung",
        ev.calculate_hit_rate(["doc_001"], ["doc_003","doc_004","doc_005"], top_k=3), 0.0))
    results.append(check("hit=0 khi doc dung o vi tri 4 (ngoai top3)",
        ev.calculate_hit_rate(["doc_001"], ["doc_003","doc_004","doc_005","doc_001"], top_k=3), 0.0))

    # ── MRR ───────────────────────────────────────────────
    print("\n[2] calculate_mrr")
    results.append(check("MRR vi tri 1 (ky vong 1.0)",
        ev.calculate_mrr(["doc_001"], ["doc_001","doc_002"]), 1.0))
    results.append(check("MRR vi tri 2 (ky vong 0.5)",
        ev.calculate_mrr(["doc_001"], ["doc_003","doc_001","doc_005"]), 0.5))
    results.append(check("MRR vi tri 3 (ky vong 0.333)",
        ev.calculate_mrr(["doc_001"], ["doc_003","doc_004","doc_001"]), 0.333, tol=0.01))
    results.append(check("MRR = 0 khi khong tim thay",
        ev.calculate_mrr(["doc_001"], ["doc_003","doc_004","doc_005"]), 0.0))

    # ── Precision@K ───────────────────────────────────────
    print("\n[3] calculate_precision_at_k")
    results.append(check("Precision@3 = 2/3 (ky vong 0.667)",
        ev.calculate_precision_at_k(["doc_001","doc_002"], ["doc_001","doc_003","doc_002"], k=3), 0.667, tol=0.01))
    results.append(check("Precision@3 = 1/3 (ky vong 0.333)",
        ev.calculate_precision_at_k(["doc_001"], ["doc_003","doc_001","doc_005"], k=3), 0.333, tol=0.01))

    # ── Recall@K ──────────────────────────────────────────
    print("\n[4] calculate_recall_at_k")
    results.append(check("Recall@5 = 2/3 (ky vong 0.667)",
        ev.calculate_recall_at_k(["doc_001","doc_002","doc_003"],
                                  ["doc_001","doc_003","doc_005","doc_007"], k=5), 0.667, tol=0.01))
    results.append(check("Recall@5 = 1.0 khi tim thay het",
        ev.calculate_recall_at_k(["doc_001","doc_002"],
                                  ["doc_001","doc_002","doc_003"], k=5), 1.0))

    # ── score() toan bo ────────────────────────────────────
    print("\n[5] score() - tich hop tat ca metrics")
    test_case = {
        "question": "Doi mat khau nhu the nao?",
        "expected_answer": "Vao Cai dat Bao mat de doi mat khau",
        "expected_retrieval_ids": ["doc_001"],
        "context": "Huong dan doi mat khau chi tiet",
    }
    response = {
        "answer": "Vao Cai dat Bao mat de doi mat khau nhanh chong.",
        "contexts": ["Vao Cai dat Bao mat de doi mat khau chi tiet cua ban."],
        "metadata": {
            "retrieved_ids": ["doc_001", "doc_002"],
            "tokens_used": 20,
        },
    }
    scores = await ev.score(test_case, response)
    print(f"  score() output: {scores}")
    has_faithfulness = "faithfulness" in scores
    has_relevancy    = "relevancy" in scores
    has_retrieval    = "retrieval" in scores
    has_hit_rate     = "hit_rate" in scores.get("retrieval", {})
    has_mrr          = "mrr" in scores.get("retrieval", {})
    for name, val in [
        ("co key 'faithfulness'", has_faithfulness),
        ("co key 'relevancy'", has_relevancy),
        ("co key 'retrieval'", has_retrieval),
        ("co key 'hit_rate' trong retrieval", has_hit_rate),
        ("co key 'mrr' trong retrieval", has_mrr),
    ]:
        icon = PASS if val else FAIL
        print(f"  {icon}  {name}")
        results.append(val)

    return results


async def test_agent():
    print("\n" + "=" * 55)
    print("  KIEM TRA agent/main_agent.py")
    print("=" * 55)
    results = []

    # Agent V1
    print("\n[6] MainAgent V1")
    v1 = MainAgent(version="v1")
    resp_v1 = await v1.query("Lam the nao de doi mat khau?")
    has_answer = bool(resp_v1.get("answer"))
    has_retrieved_ids = bool(resp_v1.get("metadata", {}).get("retrieved_ids"))
    has_contexts = bool(resp_v1.get("contexts"))
    for name, val in [
        ("co key 'answer'", has_answer),
        ("co key 'retrieved_ids' trong metadata", has_retrieved_ids),
        ("co key 'contexts'", has_contexts),
    ]:
        icon = PASS if val else FAIL
        print(f"  {icon}  {name}")
        results.append(val)
    print(f"       retrieved_ids V1: {resp_v1['metadata']['retrieved_ids']}")

    # Agent V2
    print("\n[7] MainAgent V2")
    v2 = MainAgent(version="v2")
    resp_v2 = await v2.query("Chinh sach hoan tien nhu the nao?")
    v2_ids = resp_v2.get("metadata", {}).get("retrieved_ids", [])
    v1_ids = resp_v1["metadata"]["retrieved_ids"]
    more_docs = len(v2_ids) >= len(v1_ids)
    icon = PASS if more_docs else FAIL
    print(f"  {icon}  V2 lay nhieu tai lieu hon V1 (V2={len(v2_ids)} >= V1={len(v1_ids)})")
    results.append(more_docs)
    print(f"       retrieved_ids V2: {v2_ids}")

    # evaluate_batch() tich hop
    print("\n[8] evaluate_batch() voi dataset nho")
    dataset = [
        {
            "question": "Doi mat khau?",
            "expected_answer": "Vao Cai dat Bao mat doi mat khau",
            "expected_retrieval_ids": ["doc_001"],
            "context": "Huong dan doi mat khau",
        },
        {
            "question": "Hoan tien trong bao lau?",
            "expected_answer": "Hoan tien trong 30 ngay",
            "expected_retrieval_ids": ["doc_002"],
            "context": "Chinh sach hoan tien 30 ngay",
        },
    ]
    ev = RetrievalEvaluator()
    batch_result = await ev.evaluate_batch(dataset, agent=v2)
    print(f"  evaluate_batch() output: {batch_result}")
    has_hit   = "avg_hit_rate" in batch_result
    has_mrr   = "avg_mrr" in batch_result
    has_faith = "avg_faithfulness" in batch_result
    for name, val in [
        ("co 'avg_hit_rate'", has_hit),
        ("co 'avg_mrr'", has_mrr),
        ("co 'avg_faithfulness'", has_faith),
    ]:
        icon = PASS if val else FAIL
        print(f"  {icon}  {name}")
        results.append(val)

    return results


async def main():
    r1 = await test_retrieval_eval()
    r2 = await test_agent()
    all_results = r1 + r2
    passed = sum(all_results)
    total  = len(all_results)
    print("\n" + "=" * 55)
    if passed == total:
        print(f"  [OK] TẤT CA {total}/{total} TESTS PASSED!")
        print("  Nguoi 5 da hoan thanh nhiem vu Retrieval Eval!")
    else:
        print(f"  [{total - passed} FAILED] {passed}/{total} tests passed.")
        print("  Kiem tra lai cac phan bi FAIL o tren.")
    print("=" * 55)


asyncio.run(main())
