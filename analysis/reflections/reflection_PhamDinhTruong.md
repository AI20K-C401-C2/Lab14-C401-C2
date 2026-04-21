# Reflection - Phạm Đình Trường - 2A202600255

## 1. Đóng góp cụ thể

- **Module đã implement:** Retrieval Evaluator (`engine/retrieval_eval.py`) + Nâng cấp Agent Retrieval (`agent/main_agent.py`)
- **Số commit:** (cập nhật sau khi hoàn thành)
- **Thời gian:** ~60 phút
- **Files thay đổi:**
  - `engine/retrieval_eval.py` — Implement đầy đủ Hit Rate, MRR, Precision@K, Recall@K, Faithfulness, Relevancy, score(), evaluate_batch()
  - `agent/main_agent.py` — Nâng cấp hàm `_retrieve()` trả về `retrieved_ids`, hỗ trợ V1/V2

---

## 2. Kiến thức kỹ thuật

### Hit Rate
**Hit Rate** đo xem hệ thống retrieval có lấy được ít nhất 1 tài liệu đúng trong top-k kết quả không.
- Công thức: 1.0 nếu có ≥1 expected_id trong top-k, ngược lại 0.0
- Đây là metric **binary** — chỉ quan tâm "có tìm thấy không?", không quan tâm "tìm thấy ở đâu?"
- Hạn chế: Không phân biệt giữa hệ thống tìm đúng ngay vị trí 1 hay vị trí 10.

### MRR — Mean Reciprocal Rank
**MRR** đo vị trí trung bình của kết quả đúng đầu tiên trong danh sách retrieved.
- Công thức: MRR = (1/N) × Σ (1 / rank_i)
- Ví dụ: Nếu tài liệu đúng xuất hiện ở vị trí 1 → MRR = 1.0; vị trí 2 → MRR = 0.5; vị trí 3 → MRR = 0.33
- **Tại sao MRR quan trọng hơn Hit Rate?** MRR PHÂN BIỆT chất lượng retrieval. Hệ thống luôn tìm đúng ở vị trí 1 tốt hơn hệ thống tìm đúng ở vị trí 5, dù cả hai đều có Hit Rate = 1.0.

### Precision@K vs Recall@K
| Metric | Câu hỏi trả lời | Khi nào tốt |
|--------|----------------|-------------|
| **Precision@K** | Trong top-K, bao nhiêu % là đúng? | Khi muốn kết quả sạch, không spam |
| **Recall@K** | Trong tổng số tài liệu đúng, lấy được bao nhiêu %? | Khi muốn không bỏ sót thông tin quan trọng |

**Trade-off:** Tăng K → Recall tăng nhưng Precision có thể giảm (lấy nhiều nhưng lẫn tạp).

### Faithfulness vs Relevancy (RAGAS-style)
| Metric | Đo cái gì | Chống lại |
|--------|------------|-----------|
| **Faithfulness** | Answer có bám sát context không? | Hallucination |
| **Relevancy** | Answer có liên quan đến question không? | Off-topic response |

### Tại sao đánh giá Retrieval TRƯỚC Generation?
1. **RAG = Retrieval + Generation** — nếu Retrieval sai, Generation chắc chắn sai.
2. **Debug dễ hơn:** Biết lỗi do retrieval hay do generation.
3. **Chi phí thấp:** Không cần gọi LLM để kiểm tra retrieval metrics.
4. Triết lý: *"Garbage in, garbage out"* — context xấu → câu trả lời xấu dù LLM giỏi đến đâu.

---

## 3. Trade-off Chi phí vs Chất lượng

| Lựa chọn | Chi phí | Chất lượng Retrieval |
|----------|---------|---------------------|
| **Keyword matching (đã dùng)** | Miễn phí | Trung bình — bỏ sót từ đồng nghĩa |
| **TF-IDF / BM25** | Thấp | Tốt hơn — có weighting |
| **Embedding + Vector DB** | Trung bình | Cao — hiểu ngữ nghĩa |
| **Re-ranker (Cross-Encoder)** | Cao | Rất cao — nhưng chậm |

→ Trong lab này dùng keyword matching để đơn giản. Thực tế production nên dùng Embedding + Vector DB.

---

## 4. Bài học kinh nghiệm

### Vấn đề gặp phải:
1. **`retrieved_ids` thiếu trong metadata** — Agent cũ không trả về `retrieved_ids`, khiến tất cả Retrieval Metrics = 0. Fix: Thêm `retrieved_ids` vào dict metadata trong hàm `_retrieve()`.

2. **evaluate_batch() chỉ trả về hardcode** — Placeholder cũ `return {"avg_hit_rate": 0.85, "avg_mrr": 0.72}` không có giá trị thực. Fix: Implement loop tính thực từng test case.

3. **Agent cũ không có V1/V2** — Người 6 cần V1 vs V2 để so sánh regression. Fix: Thêm `version` param và `retrieval_noise` khác nhau giữa 2 phiên bản.

### Rút ra:
- Luôn kiểm tra format output của các module liên quan trước khi implement (interface-first).
- Metrics không cần API vẫn có giá trị (keyword-based faithfulness, relevancy).
- Phân biệt được Hit Rate và MRR là yêu cầu bắt buộc để defend kỹ thuật.
