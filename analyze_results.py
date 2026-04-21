import json

with open('reports/benchmark_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

with open('reports/regression_report.json', 'r', encoding='utf-8') as f:
    regression = json.load(f)

with open('data/golden_set.jsonl', 'r', encoding='utf-8') as f:
    golden = [json.loads(l) for l in f if l.strip()]

meta_map = {g['question']: g.get('metadata', {}) for g in golden}

failed = [r for r in results if r['status'] == 'fail']
passed = [r for r in results if r['status'] == 'pass']

print("=== TONG QUAN ===")
print(f"Total: {len(results)} | Pass: {len(passed)} ({len(passed)/len(results)*100:.1f}%) | Fail: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")

# V1 metrics
v1m = regression['v1_summary']['metrics']
print(f"\n=== V1 METRICS ===")
for k, v in v1m.items():
    print(f"  {k}: {v}")

# V2 metrics
avg_score = sum(r['judge']['final_score'] for r in results) / len(results)
hit_rate = sum(r['ragas']['retrieval']['hit_rate'] for r in results) / len(results)
agreement = sum(r['judge']['agreement_rate'] for r in results) / len(results)
mrr = sum(r['ragas']['retrieval']['mrr'] for r in results) / len(results)
avg_faith = sum(r['ragas']['faithfulness'] for r in results) / len(results)
avg_rel = sum(r['ragas']['relevancy'] for r in results) / len(results)
pass_rate = len(passed) / len(results)

print(f"\n=== V2 METRICS ===")
print(f"  avg_score: {avg_score:.3f}")
print(f"  hit_rate: {hit_rate:.3f} ({hit_rate*100:.1f}%)")
print(f"  mrr: {mrr:.3f}")
print(f"  agreement_rate: {agreement:.3f} ({agreement*100:.1f}%)")
print(f"  faithfulness: {avg_faith:.3f}")
print(f"  relevancy: {avg_rel:.3f}")
print(f"  pass_rate: {pass_rate:.3f} ({pass_rate*100:.1f}%)")

# Phan loai loi
retrieval_miss = [r for r in failed if r['ragas']['retrieval']['hit_rate'] == 0.0]
irrelevant = [r for r in failed if r['ragas']['relevancy'] < 0.1]
low_faith = [r for r in failed if r['ragas']['faithfulness'] < 0.3]
incomplete = [r for r in failed if r['judge']['final_score'] == 2.0 or r['judge']['final_score'] == 2.5]

print(f"\n=== PHAN LOAI LOI ===")
print(f"Retrieval Miss (hit_rate=0): {len(retrieval_miss)} ({len(retrieval_miss)/len(failed)*100:.1f}%)")
print(f"Irrelevant (relevancy<0.1): {len(irrelevant)} ({len(irrelevant)/len(failed)*100:.1f}%)")
print(f"Hallucination (faithfulness<0.3): {len(low_faith)} ({len(low_faith)/len(failed)*100:.1f}%)")
print(f"Incomplete (score 2.0-2.5): {len(incomplete)} ({len(incomplete)/len(failed)*100:.1f}%)")

# Theo do kho
print(f"\n=== THEO DO KHO ===")
for diff in ['easy', 'medium', 'hard', 'adversarial', 'edge']:
    cases = [r for r in results if meta_map.get(r['test_case'], {}).get('difficulty') == diff]
    fails = [r for r in cases if r['status'] == 'fail']
    if cases:
        print(f"  {diff}: total={len(cases)}, fail={len(fails)}, rate={len(fails)/len(cases)*100:.0f}%")

# Score distribution
print(f"\n=== SCORE DISTRIBUTION ===")
from collections import Counter
scores = Counter(r['judge']['final_score'] for r in results)
for s in sorted(scores):
    print(f"  Score {s}: {scores[s]} cases")

# Top 3 worst
print(f"\n=== TOP 3 WORST ===")
failed_sorted = sorted(failed, key=lambda x: (x['judge']['final_score'], x['ragas']['relevancy']))
for i, r in enumerate(failed_sorted[:3]):
    meta = meta_map.get(r['test_case'], {})
    print(f"\nCase #{i+1}:")
    print(f"  Q: {r['test_case']}")
    print(f"  Diff: {meta.get('difficulty')} | Type: {meta.get('type')}")
    print(f"  A: {r['agent_response'][:150]}")
    print(f"  Score: {r['judge']['final_score']} | Judges: {r['judge']['individual_scores']}")
    print(f"  HitRate: {r['ragas']['retrieval']['hit_rate']} | MRR: {r['ragas']['retrieval']['mrr']}")
    print(f"  Faith: {r['ragas']['faithfulness']:.4f} | Rel: {r['ragas']['relevancy']:.4f}")

# All pass cases
print(f"\n=== ALL PASS CASES ===")
for i, r in enumerate(passed):
    meta = meta_map.get(r['test_case'], {})
    print(f"  [{i+1}] Score={r['judge']['final_score']} HR={r['ragas']['retrieval']['hit_rate']} Diff={meta.get('difficulty')} Q={r['test_case'][:60]}")
