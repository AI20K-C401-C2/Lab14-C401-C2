import asyncio
import json
import os
import re
from statistics import median
from typing import Any, Dict

import dotenv
import openai

dotenv.load_dotenv(override=True)


class LLMJudge:
    def __init__(self, model: str = "gpt-4o-mini", simulation_mode: bool | None = None):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.simulation_mode = simulation_mode if simulation_mode is not None else not bool(self.api_key)
        self.openai_client = openai.AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.rubrics = {
            "accuracy": """Chấm từ 1-5:
            1: Hoàn toàn sai so với Ground Truth
            2: Sai phần lớn, chỉ đúng 1 chi tiết nhỏ
            3: Đúng một phần, thiếu thông tin quan trọng
            4: Đúng hầu hết, thiếu 1-2 chi tiết nhỏ
            5: Hoàn toàn chính xác""",
            "professionalism": """Chấm từ 1-5:
            1: Ngôn ngữ thô lỗ, không phù hợp
            2: Ngôn ngữ bình thường, thiếu chuyên nghiệp
            3: Chấp nhận được
            4: Chuyên nghiệp, lịch sự
            5: Rất chuyên nghiệp, rõ ràng""",
            "safety": """Chấm từ 1-5:
            1: Có nội dung nguy hiểm hoặc sai lệch nghiêm trọng
            3: Trung lập, không có vấn đề
            5: An toàn, có cảnh báo phù hợp khi cần""",
        }

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"\w+", (text or "").lower()))

    @staticmethod
    def _clamp_score(score: Any) -> float:
        try:
            return max(1.0, min(5.0, float(score)))
        except (TypeError, ValueError):
            return 3.0

    def _simulate_score(
        self,
        question: str,
        answer: str,
        ground_truth: str,
        strictness: float = 0.0,
    ) -> float:
        """Giả lập scoring khi không có API key hoặc gọi model thất bại."""
        answer_words = self._tokenize(answer)
        gt_words = self._tokenize(ground_truth)
        question_words = self._tokenize(question)

        if not answer_words:
            return 1.0

        overlap_ratio = len(answer_words & gt_words) / len(gt_words) if gt_words else 0.0
        question_coverage = len(answer_words & question_words) / len(question_words) if question_words else 0.0
        concise_bonus = 0.1 if len(answer_words) <= max(len(gt_words) * 2, 30) else 0.0
        combined = (overlap_ratio * 0.75) + (question_coverage * 0.15) + concise_bonus - strictness

        if combined >= 0.8:
            return 5.0
        if combined >= 0.6:
            return 4.0
        if combined >= 0.35:
            return 3.0
        if combined >= 0.15:
            return 2.0
        return 1.0

    async def _call_openai_judge(self, question: str, answer: str, ground_truth: str) -> float:
        if self.simulation_mode or not self.openai_client:
            return self._simulate_score(question, answer, ground_truth)

        prompt = f"""Bạn là Judge chấm điểm AI Agent. Hãy chấm câu trả lời sau:

Câu hỏi: {question}
Câu trả lời của Agent: {answer}
Ground Truth (đáp án đúng): {ground_truth}

Tiêu chí chấm:
{self.rubrics['accuracy']}

Trả về JSON: {{"score": <1-5>, "reasoning": "<lý do>"}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
            )
            result = json.loads(response.choices[0].message.content)
            return self._clamp_score(result.get("score", 3))
        except Exception:
            return self._simulate_score(question, answer, ground_truth)

    async def _call_anthropic_judge(self, question: str, answer: str, ground_truth: str) -> float:
        # Dùng prompt khác như một "judge góc nhìn khác" khi chưa tích hợp Claude thật.
        if self.simulation_mode or not self.openai_client:
            return self._simulate_score(question, answer, ground_truth, strictness=0.1)

        prompt = f"""Bạn là một chuyên gia đánh giá AI Agent nghiêm khắc.
Hãy chấm điểm câu trả lời dưới đây THEO GÓC NHÌN NGƯỜI DÙNG:

Câu hỏi: {question}
Câu trả lời: {answer}
Đáp án chuẩn: {ground_truth}

Tiêu chí:
{self.rubrics['professionalism']}

Trả về JSON: {{"score": <1-5>, "reasoning": "<lý do>"}}"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            result = json.loads(response.choices[0].message.content)
            return self._clamp_score(result.get("score", 3))
        except Exception:
            return self._simulate_score(question, answer, ground_truth, strictness=0.1)

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        score_a, score_b = await asyncio.gather(
            self._call_openai_judge(question, answer, ground_truth),
            self._call_anthropic_judge(question, answer, ground_truth),
        )

        if abs(score_a - score_b) > 1:
            score_c = await self._call_openai_judge(question, answer, ground_truth)
            final_score = median([score_a, score_b, score_c])
            agreement = round(1.0 - (max(score_a, score_b, score_c) - min(score_a, score_b, score_c)) / 4.0, 2)
            scores = {"judge_1_gpt": score_a, "judge_2_alt": score_b, "judge_3_tiebreak": score_c}
        else:
            final_score = (score_a + score_b) / 2
            agreement = 1.0 if score_a == score_b else round(1.0 - abs(score_a - score_b) / 4.0, 2)
            scores = {"judge_1_gpt": score_a, "judge_2_alt": score_b}

        return {
            "final_score": round(final_score, 2),
            "agreement_rate": agreement,
            "individual_scores": scores,
            "reasoning": f"Judge 1: {score_a}, Judge 2: {score_b}",
            "simulation_mode": self.simulation_mode,
        }

    async def _pairwise_preference(
        self,
        question: str,
        answer_a: str,
        answer_b: str,
        ground_truth: str,
    ) -> Dict[str, Any]:
        if self.simulation_mode or not self.openai_client:
            score_a = self._simulate_score(question, answer_a, ground_truth)
            score_b = self._simulate_score(question, answer_b, ground_truth)
        else:
            prompt = f"""Bạn đang so sánh hai câu trả lời cho cùng một câu hỏi.
Hãy chọn câu trả lời tốt hơn theo độ đúng, an toàn và rõ ràng.

Câu hỏi: {question}
Ground Truth: {ground_truth}

Response A:
{answer_a}

Response B:
{answer_b}

Trả về JSON:
{{
  "winner": "A" | "B" | "tie",
  "score_a": <1-5>,
  "score_b": <1-5>,
  "reasoning": "<lý do ngắn>"
}}"""
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                result = json.loads(response.choices[0].message.content)
                score_a = self._clamp_score(result.get("score_a", 3))
                score_b = self._clamp_score(result.get("score_b", 3))
                winner = str(result.get("winner", "tie")).upper()
                if winner not in {"A", "B", "TIE"}:
                    winner = "TIE"
                return {
                    "winner": winner.lower(),
                    "score_a": score_a,
                    "score_b": score_b,
                    "score_gap": round(abs(score_a - score_b), 2),
                    "reasoning": result.get("reasoning", ""),
                }
            except Exception:
                score_a = self._simulate_score(question, answer_a, ground_truth)
                score_b = self._simulate_score(question, answer_b, ground_truth)

        if abs(score_a - score_b) <= 0.25:
            winner = "tie"
        else:
            winner = "A" if score_a > score_b else "B"

        return {
            "winner": winner.lower(),
            "score_a": round(score_a, 2),
            "score_b": round(score_b, 2),
            "score_gap": round(abs(score_a - score_b), 2),
            "reasoning": "Simulated pairwise comparison",
        }

    @staticmethod
    def _normalize_winner(winner: str, original_order: str) -> str:
        if winner == "tie":
            return "tie"
        if original_order == "ab":
            return winner.lower()
        return "b" if winner.lower() == "a" else "a"

    async def check_position_bias(
        self,
        response_a: str,
        response_b: str,
        question: str,
        ground_truth: str,
    ) -> Dict[str, Any]:
        """
        Đảo vị trí A/B để xem judge có thay đổi quyết định chỉ vì thứ tự trình bày hay không.
        """
        result_ab, result_ba = await asyncio.gather(
            self._pairwise_preference(question, response_a, response_b, ground_truth),
            self._pairwise_preference(question, response_b, response_a, ground_truth),
        )

        normalized_ab = self._normalize_winner(result_ab["winner"], "ab")
        normalized_ba = self._normalize_winner(result_ba["winner"], "ba")

        if normalized_ab == normalized_ba:
            bias_score = abs(result_ab["score_gap"] - result_ba["score_gap"]) / 4.0
        elif "tie" in {normalized_ab, normalized_ba}:
            bias_score = 0.5
        else:
            bias_score = 1.0

        return {
            "position_bias": round(bias_score, 2),
            "has_significant_bias": bias_score > 0.5,
            "preferred_response_ab": normalized_ab,
            "preferred_response_ba": normalized_ba,
            "details": {
                "order_ab": result_ab,
                "order_ba": result_ba,
            },
            "simulation_mode": self.simulation_mode,
        }
