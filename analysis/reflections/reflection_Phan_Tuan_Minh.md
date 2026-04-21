# Reflection - Phan Tuấn Minh - [2A202600422]

## 1. Đóng góp cụ thể

- **Module đã implement:** Multi-Judge Core Engine (`engine/llm_judge.py`)
- **Số commit:** (cập nhật sau khi hoàn thành)
- **Thời gian:** ~90 phút
- **Files thay đổi:**
  - `engine/llm_judge.py` — Implement đầy đủ: Rubrics chi tiết (Accuracy, Professionalism, Safety), `_call_openai_judge()`, `_call_anthropic_judge()`, `evaluate_multi_judge()` với conflict resolution, Agreement Rate
  
### Chi tiết công việc:
1. **Viết Rubrics đánh giá** — Định nghĩa 3 bộ tiêu chí chấm điểm (Accuracy, Professionalism, Safety) với thang điểm 1-5 chi tiết cho từng mức.
2. **Implement `_call_openai_judge()`** — Gọi GPT-4o-mini làm Judge #1, chấm theo tiêu chí Accuracy, trả về JSON score + reasoning.
3. **Implement `_call_anthropic_judge()`** — Gọi GPT-4o-mini với prompt khác (góc nhìn người dùng) + temperature khác (0.3) làm Judge #2, chấm theo tiêu chí Professionalism.
4. **Implement `evaluate_multi_judge()`** — Gọi 2 Judge song song bằng `asyncio.gather`, xử lý conflict khi chênh > 1 điểm (gọi Judge thứ 3, lấy median), tính Agreement Rate.

---

## 2. Kiến thức kỹ thuật

### MRR (Mean Reciprocal Rank)
- **Định nghĩa:** MRR đo vị trí trung bình của kết quả đúng đầu tiên trong danh sách retrieval.
- **Công thức:** MRR = (1/N) × Σ(1/rank_i), với rank_i là vị trí của document đúng đầu tiên cho query thứ i.
- **Ý nghĩa:** MRR = 1.0 → document đúng luôn ở vị trí đầu tiên. MRR thấp → retriever cần cải thiện ranking.
- **So với Hit Rate:** Hit Rate chỉ quan tâm "có tìm thấy hay không", MRR quan tâm "tìm thấy ở vị trí nào" → MRR nghiêm ngặt hơn.

### Cohen's Kappa
Cohen's Kappa là hệ số đo mức độ **đồng thuận giữa 2 người đánh giá**, có loại bỏ yếu tố đồng thuận do ngẫu nhiên.

- **Công thức:** κ = (Po - Pe) / (1 - Pe)
  - Po = tỷ lệ đồng thuận thực tế (observed agreement)
  - Pe = tỷ lệ đồng thuận do ngẫu nhiên (expected agreement)
- **Thang đánh giá:**
  - κ < 0.2 → Đồng thuận kém
  - 0.2 ≤ κ < 0.4 → Đồng thuận trung bình
  - 0.4 ≤ κ < 0.6 → Đồng thuận khá
  - 0.6 ≤ κ < 0.8 → Đồng thuận tốt
  - κ ≥ 0.8 → Đồng thuận rất tốt
- **Tại sao quan trọng?** Nếu chỉ dùng "% đồng ý" thì không loại trừ trường hợp 2 Judge tình cờ cho cùng điểm. Cohen's Kappa loại bỏ yếu tố may rủi này.

### Agreement Rate
Agreement Rate trong hệ thống Multi-Judge đo tỷ lệ đồng thuận giữa các Judge.

- Trong implementation của tôi:
  - `1.0` — 2 Judge cho cùng điểm
  - `0.5` — 2 Judge chênh lệch ≤ 1 điểm
  - `0.0` — 2 Judge chênh lệch > 1 điểm (conflict → gọi Judge thứ 3)
- **Ý nghĩa thực tế:** Agreement Rate cao → kết quả eval đáng tin cậy. Agreement Rate thấp → cần xem lại rubrics hoặc prompt cho Judge.

### Tại sao cần ≥ 2 Judge?
1. **Giảm bias:** Một model LLM đơn lẻ có thể có thiên vị (ví dụ: GPT thường cho điểm cao hơn Claude).
2. **Tăng độ tin cậy:** Consensus từ nhiều Judge giống như "đánh giá chéo" (peer review) trong khoa học.
3. **Phát hiện edge cases:** Một Judge có thể bỏ sót lỗi mà Judge khác phát hiện được.
4. **Thực tế production:** Các hệ thống eval chuyên nghiệp (như LMSYS Chatbot Arena) đều dùng multi-judge.

### Position Bias
- **Định nghĩa:** Judge AI có xu hướng **ưu tiên response xuất hiện trước** (vị trí đầu) trong prompt.
- **Cách detect:** Đổi chỗ Response A và Response B, so sánh kết quả. Nếu điểm thay đổi → có bias.
- **Tại sao xảy ra?** Do cách LLM được train — attention mechanism có xu hướng tập trung vào nội dung đầu tiên (primacy effect).

---

## 3. Trade-off Chi phí vs Chất lượng

| Lựa chọn | Chi phí | Chất lượng Judge |
|---|---|---|
| 1 Judge (GPT-4o-mini) | Thấp nhất | Không đáng tin — bias cao |
| 2 Judge cùng model, khác prompt (đã dùng) | Trung bình | Tốt — giảm prompt bias |
| 2 Judge khác model (GPT + Claude) | Cao | Rất tốt — giảm model bias |
| 3+ Judge + Position Bias check | Rất cao | Tuyệt vời — gần human-level |

**Lựa chọn trong lab:** Dùng 2 lần GPT-4o-mini với **prompt khác nhau** và **temperature khác nhau** (0.0 vs 0.3) để tạo đa dạng kết quả mà vẫn tiết kiệm chi phí (không cần API key Anthropic).

**Đề xuất giảm 30% chi phí:**
- Chỉ gọi Judge thứ 3 khi conflict (đã implement) — tránh gọi 3 Judge cho mọi case
- Dùng `gpt-4o-mini` thay `gpt-4o` cho Judge — rẻ hơn ~10x với quality chấp nhận được
- Cache kết quả Judge cho các câu hỏi tương tự (semantic dedup)

---

## 4. Bài học kinh nghiệm

### Vấn đề gặp phải:
1. **Thiếu `import os` và `import json`** — Code gọi `os.getenv()` và `json.loads()` nhưng quên import. Fix: Thêm import ở đầu file.
2. **Prompt gửi text trùng lặp** — Ban đầu gửi text vào cả system prompt lẫn user message, tốn gấp đôi token. Fix: Chỉ giữ 1 message role.
3. **Dead code cũ vẫn còn** — Code placeholder cũ nằm sau `return` gây confusing. Fix: Xóa sạch code cũ trước khi viết code mới.
4. **Comment indent sai** — Comment trong method bị thụt lề ngang với `async def`, dù Python vẫn chạy nhưng không professional. Fix: Thụt lề comment đúng cấp.

### Rút ra:
- **Multi-Judge là bắt buộc** trong production eval — 1 Judge đơn lẻ cho kết quả không đáng tin.
- **Conflict resolution** là yếu tố phân biệt hệ thống eval chuyên nghiệp vs nghiệp dư.
- **asyncio.gather** giúp gọi 2 Judge song song, giảm ~50% thời gian so với gọi tuần tự.
- Luôn **kiểm tra import** trước khi code — lỗi nhỏ nhưng mất thời gian debug.
