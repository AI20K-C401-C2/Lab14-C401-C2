# 📝 Reflection Cá Nhân — Phạm Việt Hoàng

## 1. Thông tin cá nhân

| Trường                  | Giá trị                          |
| ----------------------- | -------------------------------- |
| **Họ tên**              | Phạm Việt Hoàng                  |
| **Mã sinh viên**        | 2A202600274                      |
| **File đóng góp chính** | `agent/main_agent.py`, `main.py` |

---

## 2. Nhiệm vụ đã thực hiện

### 2.1 Tạo 2 phiên bản Agent (V1/V2) — `agent/main_agent.py`

Tôi đã xây dựng class `MainAgent(version)` với kiến trúc RAG mô phỏng đầy đủ:

- **Knowledge Base**: 15 tài liệu giả lập về chính sách, hướng dẫn, bảo mật, khuyến mãi...
- **V1 (Base)**:
  - Retrieval đơn giản: keyword matching, top_k=3
  - Dễ bị miss thông tin, đôi khi thêm "noise" doc ngẫu nhiên
  - Generation luôn cố trả lờii → dễ hallucination
  - Không xử lý được adversarial/edge case
- **V2 (Optimized)**:
  - Retrieval cải tiến: top_k=5, re-ranking theo category
  - Ưu tiên tài liệu bảo mật cho câu hỏi liên quan
  - Generation từ chối trả lờii khi không có context → giảm hallucination
  - Trích dẫn nguồn rõ ràng, prompt chi tiết hơn

### 2.2 Implement Release Gate Logic — `main.py`

Tôi đã viết hàm `release_decision(v1_summary, v2_summary, thresholds)` với 5 tiêu chí:

| Tiêu chí      | Ý nghĩa                                | Ngưỡng mặc định |
| ------------- | -------------------------------------- | --------------- |
| Quality Delta | V2 phải tốt hơn hoặc bằng V1           | >= 0            |
| Hit Rate      | Không cho phép retrieval tụt quá nhiều | >= -5%          |
| Agreement     | Độ đồng thuận Judge phải đủ cao        | >= 70%          |
| Latency       | Hiệu năng không được tụt quá nhiều     | <= 120% V1      |
| Cost          | Chi phí không được tăng quá nhiều      | <= 115% V1      |

Logic này tự động trả về **APPROVE** hoặc **BLOCK** kèm lý do chi tiết từng tiêu chí.

**Kết quả thực tế khi chạy benchmark 55 cases:**

- V2 đạt **APPROVE** với Delta Score +1.291, Hit Rate tăng 5.5%, Agreement Rate 90.5%

### 2.3 Tích hợp Pipeline — `main.py`

- Chạy benchmark V1 → V2 tuần tự
- Tính toán delta metrics đầy đủ
- Xuất 3 file report: `summary.json`, `benchmark_results.json`, `regression_report.json`

**Kết quả benchmark:**
| Metric | V1 | V2 | Delta |
|--------|-----|-----|-------|
| Avg Score | 1.63 | 2.92 | +1.29 |
| Hit Rate | 34.5% | 40.0% | +5.5% |
| Pass Rate | 3.6% | 65.5% | +61.8% |

---

## 3. Kiến thức đã học

### 3.1 Regression Testing là gì?

Regression Testing là quy trình **kiểm thử hồi quy** — đảm bảo phiên bản mới (V2) không làm hỏng những gì V1 đã làm tốt. Trong AI Engineering, điều này cực kỳ quan trọng vì:

- Fine-tune model mới có thể cải thiện một số case nhưng làm tệ case khác (catastrophic forgetting)
- Thay đổi prompt có thể ảnh hưởng không lường trước
- Thay đổi retrieval strategy có thể làm tăng hit_rate nhưng giảm độ chính xác câu trả lờii

### 3.2 Delta Analysis

Delta Analysis là việc **so sánh chênh lệch** giữa 2 phiên bản trên từng metric. Không chỉ nhìn điểm tuyệt đối mà phải xem:

- `ΔScore = Score_V2 - Score_V1` → Có cải thiện không?
- `ΔHitRate` → Retrieval có bị tụt không?
- `ΔLatency` → Có chậm hơn không?
- `ΔCost` → Có đắt hơn không?

### 3.3 Release Gate Criteria

Release Gate là **cổng kiểm soát** tự động quyết định có deploy V2 lên production. Các tiêu chí thường gặp:

1. **Quality Gate**: Score phải đạt ngưỡng tối thiểu
2. **Regression Gate**: Không được tụt so với V1 quá mức cho phép
3. **Performance Gate**: Latency, throughput phải chấp nhận được
4. **Cost Gate**: Chi phí inference không được vượt budget
5. **Safety Gate**: Không được tăng hallucination, toxic response

---

## 4. Thách thức & Cách giải quyết

| Thách thức                                        | Cách giải quyết                                                               |
| ------------------------------------------------- | ----------------------------------------------------------------------------- |
| Làm sao để V2 khác biệt rõ ràng V1 mà vẫn hợp lý? | Thiết kế V1 có bug cố ý (hallucination, miss retrieval) và V2 fix từng bug đó |
| Làm sao để Release Gate không quá nghiêm/ngông?   | Để ngưỡng mặc định linh hoạt, cho phép config qua tham số `thresholds`        |
| Pipeline phụ thuộc nhiều module khác              | Viết placeholder cho Evaluator và Judge, đảm bảo `main.py` vẫn chạy được      |

---

## 5. Đề xuất cải tiến

1. **Thêm Statistical Significance Test**: Dùng t-test hoặc bootstrap để kiểm tra delta có ý nghĩa thống kê không
2. **Per-case Analysis**: Không chỉ nhìn average mà xem từng case — V2 có thể tốt hơn trung bình nhưng làm tệ 5% case quan trọng nhất
3. **A/B Testing Framework**: Tích hợp traffic splitting để test V2 trên 10% user trước khi full rollout
4. **Auto-rollback**: Nếu metrics production tụt sau release, tự động rollback về V1

---

## 6. Kết luận

Qua nhiệm vụ này, tôi đã hiểu sâu hơn về:

- Cách thiết kế Agent với nhiều phiên bản để so sánh
- Tầm quan trọng của Regression Testing trong AI Engineering
- Cách xây dựng Release Gate tự động, dựa trên dữ liệu chứ không phải cảm tính
- Trade-off giữa Quality, Performance, và Cost

Tôi tin rằng những kiến thức này sẽ rất hữu ích khi làm việc với hệ thống AI thực tế.

---
