# Reflection — Bùi Minh Ngọc

**Môn học:** AI Thực Chiến | **Lab:** 14 — AI Evaluation Factory  
**Ngày:** 2026-04-21 | **Nhóm:** C (Người 7) | **Điểm phụ trách:** 15/60 (Failure Analysis)

---

## 1. Đóng góp cụ thể

| Hạng mục | Chi tiết |
|---|---|
| **Module thực hiện** | `analysis/failure_analysis.md` — Failure Analysis & 5 Whys |
| **File reflection** | `analysis/reflections/reflection_BuiMinhNgoc.md` |
| **Thời gian** | ~2 giờ (phân tích data + viết báo cáo) |

### Quy trình thực hiện

1. Chạy `python main.py` để benchmark 55 test cases qua pipeline V1 & V2
2. Đọc kết quả từ `reports/benchmark_results.json`: 12 pass, 43 fail
3. Phân loại 43 fail cases theo 4 nhóm: Retrieval Miss (31), Irrelevant (19), Incomplete (18), Hallucination (0)
4. Phân tích theo độ khó: Easy 73%, Medium 80%, Hard 70%, Adversarial 90%, Edge 80%
5. Chọn 3 case tệ nhất (score = 1.0) → áp dụng **5 Whys** truy nguyên root cause
6. Phân tích 12 pass cases → tìm ra pattern: tất cả đều là keyword matching trực tiếp
7. Đề xuất Action Plan 6 mục cải tiến cụ thể, ưu tiên theo impact

---

## 2. Kiến thức kỹ thuật

### 2.1 MRR (Mean Reciprocal Rank)

**Định nghĩa:** Đo mức độ tìm đúng document VÀ đúng vị trí đầu tiên.

**Cách tính:**
- Với mỗi query, tìm vị trí (rank) của document đúng đầu tiên trong danh sách kết quả
- MRR = trung bình của 1/rank trên tất cả queries

**Ví dụ trong lab (V2):**
- Tổng MRR = 0.303 → nghĩa là trung bình document đúng nằm ở vị trí thứ ~3.3
- Khi Hit Rate = 1.0 nhưng MRR = 0.333 → Agent tìm đúng nhưng ở vị trí thứ 3, không phải đầu tiên
- Khi Hit Rate = 0.0 → MRR = 0 (không tìm thấy gì)

**Ý nghĩa thực tế:** MRR thấp (0.303) cho thấy ngay cả khi Agent tìm đúng document, nó thường không nằm ở vị trí top-1. Vì `_generate()` lấy `contexts[0]`, điều này gây ra câu trả lời sai dù retrieval đúng.

---

### 2.2 Cohen's Kappa / Agreement Rate

**Vấn đề:** Khi dùng Multi-Judge (2+ Judge), cần đo các Judge có đồng thuận hay không.

**Cách tính trong lab (LLMJudge):**
```
Nếu |score_A - score_B| == 0 → agreement = 1.0 (hoàn toàn đồng ý)
Nếu |score_A - score_B| > 0  → agreement = 1.0 - |diff| / 4.0
Nếu |score_A - score_B| > 1  → gọi Judge thứ 3, dùng median để tiebreak
```

**Kết quả lab:**
- V1 Agreement: 84.1% → V2 Agreement: 89.1% → **V2 nhất quán hơn**
- Meaning: Các câu trả lời rõ ràng hơn → 2 Judge dễ đồng thuận hơn
- 89.1% > 70% threshold → đủ tin cậy để dùng kết quả judge

**Cohen's Kappa** bổ sung: Loại trừ factor "agreement by chance":
$$\kappa = \frac{p_o - p_e}{1 - p_e}$$
- κ > 0.8 = "almost perfect agreement"
- κ 0.6-0.8 = "substantial agreement"

---

### 2.3 Position Bias

**Hiện tượng:** LLM Judge thiên vị câu trả lời xuất hiện ở vị trí A (đầu tiên), bất kể chất lượng.

**Cách detect trong lab (`check_position_bias`):**
1. So sánh A vs B theo thứ tự gốc → judge chọn winner
2. Đảo vị trí: B vs A → judge lại chọn winner
3. Nếu winner đổi theo vị trí (không theo nội dung) → có Position Bias

**Ví dụ:**
- Lần 1: "Response A: [tốt], Response B: [kém]" → Judge chọn A ✅
- Lần 2: "Response A: [kém], Response B: [tốt]" → Judge vẫn chọn A ❌ (bias!)

**Tại sao quan trọng:** Nếu Judge có bias, evaluation pairwise comparison không đáng tin. Multi-Judge với 2+ model khác nhau giảm thiểu rủi ro này vì mỗi model có bias pattern khác nhau.

---

## 3. Trade-off Chi Phí vs Chất Lượng

| Cấu hình | Chi phí / 55 cases | Quality | Tốc độ |
|---|:-:|:-:|:-:|
| Simulation mode | $0 | ⭐ (Fixed score 2.5) | Instant |
| GPT-4o-mini (2 Judge) | ~$0.01-0.02 | ⭐⭐⭐⭐ (Scores hợp lý, Agreement 89.1%) | ~40s |
| GPT-4o-mini + GPT-4o | ~$0.10-0.15 | ⭐⭐⭐⭐⭐ (Multi-perspective) | ~90s |
| GPT-4o Full | ~$0.30-0.50 | ⭐⭐⭐⭐⭐ | ~120s |

**Quan sát thực tế trong lab:**
- Dùng GPT-4o-mini cho cả 2 Judge → Agreement 89.1%, kết quả phân biệt rõ pass/fail → **đủ tốt**
- Chi phí gần như bằng 0 cho 55 cases → phù hợp khi iterate nhanh
- Chỉ cần GPT-4o khi muốn tiebreaker thật sự hay cần evaluation chất lượng cao nhất

**Kết luận:** GPT-4o-mini là sweet spot cho evaluation pipeline nhỏ-trung bình (<1000 cases).

---

## 4. Bài Học Kinh Nghiệm

### 4.1 Vấn đề gặp phải & cách giải quyết

| Vấn đề | Nguyên nhân | Cách xử lý |
|---|---|---|
| `main.py` hard-code `simulation_mode=True` | Code cũ chưa load `.env` | Thêm `dotenv.load_dotenv()` ở đầu file, để `LLMJudge()` tự detect |
| `golden_set.jsonl` chỉ có 1 sample | File chưa được generate | Chạy `python data/synthetic_gen.py` → 55 cases |
| UnicodeEncodeError trên Windows | Terminal Windows dùng cp1252, không hỗ trợ emoji/tiếng Việt | Set `PYTHONIOENCODING=utf-8` trước khi chạy |
| Hit Rate = 0 ban đầu | Chạy simulation mode → score giả lập cố định | Fix `.env` loading → API key thật → kết quả thực |

### 4.2 Insight quan trọng nhất

> **"Retrieval quality quyết định ceiling của toàn bộ RAG pipeline."**
> 
> 72.1% lỗi đến từ Retrieval Miss. 0% đến từ Hallucination. Agent không bịa — nó chỉ **tìm sai rồi copy**. Cải thiện retrieval (keyword → semantic) sẽ có impact lớn hơn bất kỳ cải thiện nào ở tầng generation.

### 4.3 5 Whys: Bài học phương pháp luận

- **5 Whys giúp tránh kết luận bề mặt.** Nếu dừng ở "Agent trả lời sai" → fix sai chỗ. Drill down 5 lần → phát hiện root cause thật sự ở Retrieval/KB coverage.
- **Case #3 là case hay nhất:** Hit Rate = 1.0, MRR = 1.0 (retrieve đúng 100%) nhưng Score vẫn 1.0/5 → chứng minh retrieval đúng chưa đủ, cần generation quality.

### 4.4 Kỹ năng phát triển

- Đọc và phân tích JSON benchmark ở quy mô 55 cases
- Áp dụng Root Cause Analysis (5 Whys) vào AI pipeline
- Hiểu sâu pipeline RAG: Ingestion → Retrieval → Generation → Evaluation
- Phân biệt các loại lỗi: Retrieval Miss vs Hallucination vs Incomplete
- Git workflow: branch riêng (BuiMinhNgoc), commit, push

---

## 5. Tổng Kết

Lab 14 giúp tôi hiểu rằng **đánh giá AI là một kỹ thuật riêng (AI Evaluation Engineering)**, không chỉ đơn giản là "xem đúng hay sai". Evaluation Factory với Multi-Judge, Retrieval Metrics, và Regression Testing cho phép đo lường có hệ thống, phát hiện root cause, và ra quyết định Release/Rollback dựa trên dữ liệu thay vì cảm tính.

Failure Analysis là bước không thể thiếu: biết *tại sao fail* (root cause) quan trọng hơn biết *bao nhiêu % fail*.
