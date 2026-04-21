

import asyncio
import random
from typing import List, Dict, Tuple

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

ALL_DOC_IDS = list(KNOWLEDGE_BASE.keys())


class MainAgent:

    def __init__(self, version: str = "v1"):
        self.version = version
        self.name = f"SupportAgent-{version}"

        if version == "v2":
            self.system_prompt = (
                "Bạn là trợ lý hỗ trợ khách hàng chuyên nghiệp. "
                "CHỈ trả lờii dựa trên context được cung cấp. "
                "Nếu không có thông tin, hãy nói thật thay vì đoán."
            )
            self.retrieval_noise = 0.1
            self.top_k = 5
        else:
            self.system_prompt = "Bạn là trợ lý hỗ trợ khách hàng."
            self.retrieval_noise = 0.3
            self.top_k = 3

    def _retrieve(self, question: str) -> Tuple[List[str], List[str]]:

        question_words = set(question.lower().split())

        scores = {}
        for doc_id, content in KNOWLEDGE_BASE.items():
            doc_words = set(content.lower().split())
            overlap = len(question_words & doc_words)
            scores[doc_id] = overlap

        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[: self.top_k]

        retrieved_ids = [doc_id for doc_id, _ in top_docs]
        contexts = [KNOWLEDGE_BASE[doc_id] for doc_id in retrieved_ids]

        if retrieved_ids and random.random() < self.retrieval_noise:
            retrieved_ids = retrieved_ids[1:]
            contexts = contexts[1:]

        return retrieved_ids, contexts

    def _generate(self, question: str, contexts: List[str]) -> str:
        if not contexts:
            return f"Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn."

        main_context = contexts[0]

        if self.version == "v2":
            return (
                f"Dựa trên tài liệu hệ thống: {main_context} "
                f"Nếu bạn cần thêm thông tin về '{question}', vui lòng liên hệ hỗ trợ."
            )
        else:
            return f"Câu trả lờii: {main_context}"

    async def query(self, question: str) -> Dict:
   
        await asyncio.sleep(0.1)

        retrieved_ids, contexts = self._retrieve(question)

        answer = self._generate(question, contexts)

        return {
            "answer": answer,
            "contexts": contexts,
            "metadata": {
                "model": "gpt-4o-mini" if self.version == "v2" else "gpt-3.5-turbo",
                "tokens_used": len(answer.split()),
                "retrieved_ids": retrieved_ids,   
                "sources": retrieved_ids,
                "version": self.version,
            },
        }


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
