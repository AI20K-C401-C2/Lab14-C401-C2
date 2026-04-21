# Báo cáo Cá nhân (Reflection) - Lab 14

**Họ và tên:** Phạm Việt Anh
**Nhóm phụ trách:** Nhóm B (Dataset & Retrieval Eval)
**Vai trò:** Thiết kế Golden Dataset & SDG (Synthetic Data Generation)

---

## 1. Mức độ đóng góp kỹ thuật (Engineering Contribution) 
Trong Lab 14, nhiệm vụ cốt lõi của tôi là xây dựng bộ dữ liệu chuẩn (Golden Dataset) đảm bảo độ phủ và độ khó làm nền tảng đánh giá hiệu năng toàn bộ hệ thống Agent. Chi tiết:

- **Xây dựng Knowledge Base (KB):** Thiết kế cấu trúc `KNOWLEDGE_BASE` trong `data/synthetic_gen.py` bao gồm 15 tài liệu giả lập các bối cảnh thực tế của doanh nghiệp (Chính sách hoàn tiền, Hướng dẫn bảo mật, Gói dịch vụ Premium...).
- **Phát triển 55+ Test Cases Đa dạng:** Lập trình hàm `build_golden_dataset()` tạo ra tổng cộng 55 test cases được phân bổ cân bằng:
  - 15 Easy (Fact-check)
  - 15 Medium (Reasoning)
  - 10 Hard (Multi-source)
  - 10 Adversarial (Red teaming)
  - 5 Edge Cases (Biên)
- **Mapping Ground Truth:** Mọi test case đều được đính kèm `expected_retrieval_ids` cụ thể để phục vụ việc tính toán các chỉ số Retrieval metrics (Hit Rate, MRR, Recall@K) mà Người 5 nhóm B phụ trách.
- **Tích hợp Siêu dữ liệu (Metadata):** Áp dụng metadata mapping (như `difficulty`, `type`, `category`) giúp ở những phần việc sau Nhóm C có thể filter báo cáo Failure Clustering chi tiết.

## 2. Chiều sâu kỹ thuật (Technical Depth) 

### A. Tại sao việc đưa Adversarial Cases vào Dataset lại cực kỳ quan trọng?
Một AI Agent ứng dụng cho môi trường Production (như chăm sóc khách hàng) sẽ phải đối mặt với nhiều luồng thông tin "độc hại" từ người dùng. Việc thiết kế Adversarial Cases (như Prompt Injection, Goal Hijacking hay Social Engineering) nhằm **Stress Test độ an toàn (Safety) và sự tuân thủ (Faithfulness)** của hệ thống. Nhờ các test case này, nếu Agent bị thao túng để thay đổi điều khoản dịch vụ hoặc rò rỉ prompt, Pipeline sẽ ghi nhận tỷ lệ thất bại cao – từ đó chặn quá trình Release tự động ở Regression Gate.

### B. Chiến lược thiết kế Golden Dataset chuẩn xác
Việc có một dataset Benchmark chất lượng đỏi hỏi chiến lược:
1. **Difficulty Scaling:** Nếu chỉ có các truy vấn thông thường, Pipeline sẽ trả về điểm số ảo (bias). Phải thiết kế những câu hỏi (Multi-source) đòi hỏi Retriever cần lấy ít nhất 2-3 tài liệu rải rác mới trả lời được, giúp nhận thấy rõ điểm yếu của khâu Chunking.
2. **Ground Truth Mapping Rõ Ràng:** Không chỉ là đánh giá Generation, RAG framework yêu cầu khả năng đánh giá Retrieval. Bằng cách nối (map) mỗi text về đúng tài liệu nào chịu trách nhiệm (VD: `doc_001`), quá trình tính MRR (Mean Reciprocal Rank) mới có ý nghĩa.

## 3. Kỹ năng giải quyết vấn đề (Problem Solving) 

**Vấn đề gặp phải:** Trong quá trình thiết kế Edge Cases, có các câu hỏi cố tình đẩy Agent vào trường hợp Out-of-Context (hỏi điêu, hỏi không liên quan) hoặc Ambiguous (câu hỏi mập mờ). Rất dễ để Eval Engine tự động chấm điểm thấp nếu Agent không đưa lời giải.

**Giải pháp đề xuất & Thực thi:** 
Tôi đã thiết kế các `expected_answer` trong Golden Dataset định hình việc **từ chối lịch sự, xác nhận phạm vi kiến thức** (VD: "Xin lỗi, câu hỏi này nằm ngoài phạm vi hỗ trợ..."). 
Điểm mạnh của hướng tiếp cận này:
- Quản trị được rủi ro bịa đặt thông tin (Hallucination) từ LLM sinh câu trả lời.
- Giúp khối lượng công việc của Multi-Judge Engine (Nhóm A) dễ dàng align tiêu chí "Sự chuyên nghiệp" (Professionalism) mà không bị xung đột logic trong việc Agent từ chối cung cấp kết quả.
- Đảm bảo điểm số ở nhóm Edge Cases phản ánh đúng "Chất lượng xử lý thông tin", phân biệt rõ với "Không biết trả lời".
