"""
agent/main_agent.py
Người phụ trách:
  - Người 6 (Phạm Việt Hoàng): Class MainAgent(version), V1 vs V2
  - Người 5 (Phạm Đình Trường): Nâng cấp hàm _retrieve trả về retrieved_ids
"""

import asyncio
import random
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Base giả lập (Người 4 sẽ cung cấp bản thật từ synthetic_gen.py)
# Người 5 dùng bản này để test retrieval simulation.
# ─────────────────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = {
    "doc_001": "Hướng dẫn đổi mật khẩu: Vào Cài đặt > Bảo mật > Đổi mật khẩu. Nhập mật khẩu cũ và mật khẩu mới.",
    "doc_002": "Chính sách hoàn tiền: Khách hàng được hoàn tiền trong vòng 30 ngày kể từ ngày mua hàng.",
    "doc_003": "Gói dịch vụ Premium: Bao gồm hỗ trợ 24/7, giá 199.000đ/tháng. Nâng cấp tại Tài khoản > Gói dịch vụ.",
    "doc_004": "Cách liên hệ hỗ trợ: Gọi hotline 1800-xxxx (miễn phí) hoặc chat trực tuyến trong giờ hành chính.",
    "doc_005": "Điều khoản sử dụng: Nghiêm cấm chia sẻ tài khoản. Vi phạm có thể bị khóa tài khoản vĩnh viễn.",
    "doc_006": "Hướng dẫn thanh toán: Hỗ trợ Visa, Mastercard, chuyển khoản ngân hàng, ví MoMo, ZaloPay.",
    "doc_007": "Chính sách bảo mật dữ liệu: Dữ liệu được mã hóa AES-256. Không chia sẻ với bên thứ ba khi chưa có sự đồng ý.",
    "doc_008": "Câu hỏi thường gặp: Tài khoản bị khóa? Liên hệ hỗ trợ theo quy trình tại Trợ giúp > Khôi phục tài khoản.",
    "doc_009": "Hướng dẫn cài đặt ứng dụng iOS: Tải từ App Store, tìm kiếm 'SupportApp', cài đặt và đăng nhập.",
    "doc_010": "Hướng dẫn cài đặt ứng dụng Android: Tải từ CH Play, tìm kiếm 'SupportApp', cấp quyền truy cập cần thiết.",
    "doc_011": "Chính sách đổi trả hàng hóa: Hàng hóa còn nguyên tem nhãn được đổi trả trong 7 ngày.",
    "doc_012": "Hướng dẫn kích hoạt tài khoản: Email kích hoạt gửi trong vòng 5 phút. Kiểm tra mục Spam nếu không thấy.",
    "doc_013": "Tính năng Two-Factor Authentication (2FA): Bật 2FA tại Cài đặt > Bảo mật > Xác thực 2 bước.",
    "doc_014": "Gói dịch vụ Cơ bản: Miễn phí, giới hạn 10 yêu cầu/ngày. Không có hỗ trợ qua điện thoại.",
    "doc_015": "Lịch sử giao dịch: Xem tại mục Tài khoản > Lịch sử giao dịch. Có thể lọc theo ngày và loại giao dịch.",
}

# Danh sách tất cả doc_ids để giả lập retrieval
ALL_DOC_IDS = list(KNOWLEDGE_BASE.keys())


class MainAgent:
    """
    Agent hỗ trợ khách hàng với RAG pipeline.

    Người 6 (Phạm Việt Hoàng): Tạo V1/V2, Release Gate.
    Người 5 (Phạm Đình Trường): Nâng cấp _retrieve để trả về retrieved_ids
                                 (bắt buộc cho Retrieval Evaluation).
    """

    def __init__(self, version: str = "v1"):
        self.version = version
        self.name = f"SupportAgent-{version}"

        if version == "v2":
            # V2: Tốt hơn — ít bị bỏ sót tài liệu hơn
            self.system_prompt = (
                "Bạn là trợ lý hỗ trợ khách hàng chuyên nghiệp. "
                "CHỈ trả lời dựa trên context được cung cấp. "
                "Nếu không có thông tin, hãy nói thật thay vì đoán."
            )
            self.retrieval_noise = 0.1   # 10% miss rate → tốt hơn V1
            self.top_k = 5               # Lấy nhiều tài liệu hơn
        else:
            # V1: Cơ bản — dễ bỏ sót tài liệu
            self.system_prompt = "Bạn là trợ lý hỗ trợ khách hàng."
            self.retrieval_noise = 0.3   # 30% miss rate
            self.top_k = 3               # Lấy ít tài liệu hơn

    # ─────────────────────────────────────────────
    # NGƯỜI 5 PHỤ TRÁCH: Nâng cấp _retrieve
    # ─────────────────────────────────────────────
    def _retrieve(self, question: str) -> Tuple[List[str], List[str]]:
        """
        Giả lập bước Retrieval: tìm tài liệu liên quan đến câu hỏi.

        - V2 ít bỏ sót hơn V1 (retrieval_noise thấp hơn).
        - Trả về (retrieved_ids, contexts) — retrieved_ids QUAN TRỌNG cho Retrieval Eval.

        Logic:
          1. Tính keyword overlap giữa câu hỏi và từng tài liệu.
          2. Lấy top_k tài liệu có overlap cao nhất.
          3. Với xác suất retrieval_noise, bỏ sót 1 tài liệu (giả lập lỗi).
        """
        question_words = set(question.lower().split())

        # Tính điểm overlap từ khóa
        scores = {}
        for doc_id, content in KNOWLEDGE_BASE.items():
            doc_words = set(content.lower().split())
            overlap = len(question_words & doc_words)
            scores[doc_id] = overlap

        # Sắp xếp theo điểm overlap, lấy top_k
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[: self.top_k]

        retrieved_ids = [doc_id for doc_id, _ in top_docs]
        contexts = [KNOWLEDGE_BASE[doc_id] for doc_id in retrieved_ids]

        # Giả lập lỗi retrieval theo retrieval_noise
        if retrieved_ids and random.random() < self.retrieval_noise:
            # Bỏ sót tài liệu đầu tiên (tài liệu quan trọng nhất)
            retrieved_ids = retrieved_ids[1:]
            contexts = contexts[1:]

        return retrieved_ids, contexts

    def _generate(self, question: str, contexts: List[str]) -> str:
        """
        Giả lập bước Generation: sinh câu trả lời từ context.
        (Thực tế sẽ gọi LLM như GPT-4o, Claude...)
        """
        if not contexts:
            return f"Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn."

        # Lấy context đầu tiên (đơn giản nhất)
        main_context = contexts[0]

        if self.version == "v2":
            # V2: Trả lời chi tiết hơn, bám sát context hơn
            return (
                f"Dựa trên tài liệu hệ thống: {main_context} "
                f"Nếu bạn cần thêm thông tin về '{question}', vui lòng liên hệ hỗ trợ."
            )
        else:
            # V1: Trả lời đơn giản hơn
            return f"Câu trả lời: {main_context}"

    async def query(self, question: str) -> Dict:
        """
        Pipeline RAG đầy đủ:
          1. _retrieve: tìm tài liệu liên quan
          2. _generate: sinh câu trả lời

        Returns dict với đầy đủ thông tin cho RetrievalEvaluator.score()
        """
        # Giả lập độ trễ mạng / LLM call
        await asyncio.sleep(0.1)

        # 1. Retrieval
        retrieved_ids, contexts = self._retrieve(question)

        # 2. Generation
        answer = self._generate(question, contexts)

        return {
            "answer": answer,
            "contexts": contexts,
            "metadata": {
                "model": "gpt-4o-mini" if self.version == "v2" else "gpt-3.5-turbo",
                "tokens_used": len(answer.split()),
                "retrieved_ids": retrieved_ids,   # ← QUAN TRỌNG cho Retrieval Eval
                "sources": retrieved_ids,
                "version": self.version,
            },
        }


# ─────────────────────────────────────────────
# Test nhanh khi chạy trực tiếp
# ─────────────────────────────────────────────
if __name__ == "__main__":
    async def test():
        print("=== Test Agent V1 ===")
        agent_v1 = MainAgent(version="v1")
        resp_v1 = await agent_v1.query("Làm thế nào để đổi mật khẩu tài khoản?")
        print(f"Answer: {resp_v1['answer']}")
        print(f"Retrieved IDs: {resp_v1['metadata']['retrieved_ids']}")

        print("\n=== Test Agent V2 ===")
        agent_v2 = MainAgent(version="v2")
        resp_v2 = await agent_v2.query("Chính sách hoàn tiền như thế nào?")
        print(f"Answer: {resp_v2['answer']}")
        print(f"Retrieved IDs: {resp_v2['metadata']['retrieved_ids']}")

    asyncio.run(test())
