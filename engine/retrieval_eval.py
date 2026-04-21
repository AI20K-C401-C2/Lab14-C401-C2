"""
engine/retrieval_eval.py
Người phụ trách: Người 5 — Phạm Đình Trường
Nhiệm vụ: Implement các metrics đánh giá retrieval cho RAG pipeline.
  - Hit Rate
  - MRR (Mean Reciprocal Rank)
  - Precision@K
  - Recall@K
  - RAGAS-style: Faithfulness & Relevancy
"""

from typing import List, Dict


class RetrievalEvaluator:
    """
    Đánh giá chất lượng phần Retrieval trong RAG pipeline.

    Các metrics:
      - hit_rate   : Có lấy được ít nhất 1 tài liệu đúng không?
      - mrr        : Vị trí trung bình của tài liệu đúng đầu tiên (1/rank).
      - precision@k: Trong top-k kết quả, bao nhiêu % là đúng?
      - recall@k   : Trong các tài liệu đúng, lấy được bao nhiêu %?
      - faithfulness: Câu trả lời có bám sát context không?
      - relevancy  : Câu trả lời có liên quan đến câu hỏi không?
    """

    def __init__(self):
        pass

    # ─────────────────────────────────────────────
    # 1. HIT RATE
    # ─────────────────────────────────────────────
    def calculate_hit_rate(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        top_k: int = 3,
    ) -> float:
        """
        Tính Hit Rate: ít nhất 1 expected_id có nằm trong top_k retrieved_ids không?
        Trả về 1.0 (có) hoặc 0.0 (không).

        Ví dụ:
            expected_ids  = ["doc_001", "doc_002"]
            retrieved_ids = ["doc_003", "doc_001", "doc_005"]
            top_k = 3 → hit = True → 1.0
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    # ─────────────────────────────────────────────
    # 2. MRR — Mean Reciprocal Rank
    # ─────────────────────────────────────────────
    def calculate_mrr(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
    ) -> float:
        """
        Tính MRR: 1 / vị trí (1-indexed) của expected_id đầu tiên tìm thấy.
        Nếu không tìm thấy → 0.0.

        Ví dụ:
            expected_ids  = ["doc_001"]
            retrieved_ids = ["doc_003", "doc_001", "doc_005"]
            → doc_001 ở vị trí 2 → MRR = 1/2 = 0.5
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    # ─────────────────────────────────────────────
    # 3. PRECISION@K
    # ─────────────────────────────────────────────
    def calculate_precision_at_k(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        k: int = 3,
    ) -> float:
        """
        Precision@K = (số tài liệu đúng trong top-k) / k

        Khác Hit Rate: Hit Rate chỉ cần 1 tài liệu đúng (binary).
        Precision@K đo tỉ lệ CHÍNH XÁC trong nhóm kết quả.

        Ví dụ:
            expected_ids  = ["doc_001", "doc_002"]
            retrieved_ids = ["doc_001", "doc_003", "doc_002"]
            k=3 → 2 tài liệu đúng / 3 = 0.667
        """
        top_k = retrieved_ids[:k]
        relevant = sum(1 for doc_id in top_k if doc_id in expected_ids)
        return relevant / k if k > 0 else 0.0

    # ─────────────────────────────────────────────
    # 4. RECALL@K
    # ─────────────────────────────────────────────
    def calculate_recall_at_k(
        self,
        expected_ids: List[str],
        retrieved_ids: List[str],
        k: int = 5,
    ) -> float:
        """
        Recall@K = (số expected_id tìm thấy trong top-k) / tổng số expected_id

        Ý nghĩa: Hệ thống thu hồi được bao nhiêu % tài liệu cần thiết?

        Ví dụ:
            expected_ids  = ["doc_001", "doc_002", "doc_003"]
            retrieved_ids = ["doc_001", "doc_003", "doc_005", "doc_007"]
            k=5 → tìm thấy 2/3 = 0.667
        """
        if not expected_ids:
            return 1.0
        top_k = retrieved_ids[:k]
        found = sum(1 for doc_id in expected_ids if doc_id in top_k)
        return found / len(expected_ids)

    # ─────────────────────────────────────────────
    # 5. FAITHFULNESS (RAGAS-style, không cần API)
    # ─────────────────────────────────────────────
    def _calculate_faithfulness(
        self,
        answer: str,
        contexts: List[str],
        expected_answer: str,
    ) -> float:
        """
        Đo mức độ câu trả lời BÁM SÁT context (không hallucinate).
        Phương pháp đơn giản: đếm từ chung giữa answer và contexts.

        Giá trị: 0.0 (hallucinate hoàn toàn) → 1.0 (hoàn toàn từ context).
        """
        if not contexts:
            return 0.0
        # Gộp tất cả context thành 1 chuỗi
        all_context_text = " ".join(contexts).lower()
        answer_words = set(answer.lower().split())
        context_words = set(all_context_text.split())

        if not answer_words:
            return 0.0

        # Tỉ lệ từ trong answer mà xuất hiện trong context
        overlap = answer_words & context_words
        return len(overlap) / len(answer_words)

    # ─────────────────────────────────────────────
    # 6. RELEVANCY (RAGAS-style, không cần API)
    # ─────────────────────────────────────────────
    def _calculate_relevancy(
        self,
        question: str,
        answer: str,
        expected_answer: str,
    ) -> float:
        """
        Đo mức độ câu trả lời LIÊN QUAN đến câu hỏi.
        Phương pháp: đo độ tương đồng từ vựng giữa answer và expected_answer.

        Giá trị: 0.0 (không liên quan) → 1.0 (hoàn toàn đúng).
        """
        answer_words = set(answer.lower().split())
        expected_words = set(expected_answer.lower().split())

        if not expected_words:
            return 1.0

        overlap = answer_words & expected_words
        # Jaccard similarity
        return len(overlap) / len(answer_words | expected_words)

    # ─────────────────────────────────────────────
    # 7. HÀM CHÍNH: score() — tích hợp tất cả metrics
    # ─────────────────────────────────────────────
    async def score(self, test_case: Dict, response: Dict) -> Dict:
        """
        Tính toàn bộ metrics cho 1 test case.

        Args:
            test_case: dict có keys: question, expected_answer, expected_retrieval_ids
            response : dict trả về từ Agent.query(), có keys: answer, contexts, metadata

        Returns:
            dict chứa faithfulness, relevancy, và các retrieval metrics
        """
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = response.get("metadata", {}).get("retrieved_ids", [])
        answer = response.get("answer", "")
        contexts = response.get("contexts", [])
        expected_answer = test_case.get("expected_answer", "")
        question = test_case.get("question", "")

        hit_rate = self.calculate_hit_rate(expected_ids, retrieved_ids, top_k=3)
        mrr = self.calculate_mrr(expected_ids, retrieved_ids)
        precision_at_3 = self.calculate_precision_at_k(expected_ids, retrieved_ids, k=3)
        recall_at_5 = self.calculate_recall_at_k(expected_ids, retrieved_ids, k=5)
        faithfulness = self._calculate_faithfulness(answer, contexts, expected_answer)
        relevancy = self._calculate_relevancy(question, answer, expected_answer)

        return {
            "faithfulness": round(faithfulness, 4),
            "relevancy": round(relevancy, 4),
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": round(mrr, 4),
                "precision_at_3": round(precision_at_3, 4),
                "recall_at_5": round(recall_at_5, 4),
            },
        }

    # ─────────────────────────────────────────────
    # 8. ĐÁNH GIÁ TOÀN BỘ DATASET
    # ─────────────────────────────────────────────
    async def evaluate_batch(self, dataset: List[Dict], agent=None) -> Dict:
        """
        Chạy eval cho toàn bộ dataset.
        Nếu agent được truyền vào, sẽ gọi agent.query() cho từng case.
        Nếu không, dùng response giả để tính metrics từ expected_retrieval_ids.

        Returns:
            {
                "avg_hit_rate": float,
                "avg_mrr": float,
                "avg_precision_at_3": float,
                "avg_recall_at_5": float,
                "avg_faithfulness": float,
                "avg_relevancy": float,
                "total_cases": int,
            }
        """
        all_scores = []

        for test_case in dataset:
            if agent is not None:
                response = await agent.query(test_case["question"])
            else:
                # Fallback: tạo response giả để kiểm tra metrics retrieval
                expected_ids = test_case.get("expected_retrieval_ids", [])
                response = {
                    "answer": test_case.get("expected_answer", ""),
                    "contexts": [test_case.get("context", "")],
                    "metadata": {"retrieved_ids": expected_ids, "tokens_used": 50},
                }

            scores = await self.score(test_case, response)
            all_scores.append(scores)

        n = len(all_scores) if all_scores else 1

        return {
            "avg_hit_rate": round(
                sum(s["retrieval"]["hit_rate"] for s in all_scores) / n, 4
            ),
            "avg_mrr": round(
                sum(s["retrieval"]["mrr"] for s in all_scores) / n, 4
            ),
            "avg_precision_at_3": round(
                sum(s["retrieval"]["precision_at_3"] for s in all_scores) / n, 4
            ),
            "avg_recall_at_5": round(
                sum(s["retrieval"]["recall_at_5"] for s in all_scores) / n, 4
            ),
            "avg_faithfulness": round(
                sum(s["faithfulness"] for s in all_scores) / n, 4
            ),
            "avg_relevancy": round(
                sum(s["relevancy"] for s in all_scores) / n, 4
            ),
            "total_cases": n,
        }
