# Failure Analysis — Lab 14: AI Evaluation Factory

**Tác giả:** Bùi Minh Ngọc (Người 7 — Nhóm C)  
**Ngày phân tích:** 2026-04-21  
**Nguồn dữ liệu:** `reports/benchmark_results.json`, `reports/summary.json`, `reports/regression_report.json`

---

## Section 1 — Tổng Quan Benchmark

### 1.1 Kết quả so sánh Regression (V1 vs V2)

| Metric | Agent V1 (Base) | Agent V2 (Optimized) | Delta | Đánh giá |
|--------|:-:|:-:|:-:|---|
| **Avg Score (1-5)** | 1.809 | 2.036 | +0.227 | ✅ V2 tốt hơn |
| **Hit Rate** | 38.2% | 36.4% | -1.8% | ⚠️ V2 giảm nhẹ (trong threshold) |
| **MRR** | — | 0.303 | — | Document đúng thường ở vị trí thứ 3+ |
| **Agreement Rate** | 84.1% | 89.1% | +5.0% | ✅ Judge nhất quán hơn |
| **Faithfulness** | — | 0.481 | — | Trung thành ~48% với context |
| **Relevancy** | — | 0.125 | — | ⛔ Chỉ 12.5% câu trả lời relevant |
| **Pass Rate** | 20.0% | 21.8% | +1.8% | ✅ Cải thiện nhẹ |
| **Avg Latency** | 0.109s | 0.108s | -0.001s | ✅ Tương đương |

### 1.2 Phân bố Pass/Fail (V2 — 55 cases)

| Trạng thái | Số cases | Tỷ lệ |
|---|:-:|:-:|
| ✅ Pass (score ≥ 3.0) | 12 | 21.8% |
| ❌ Fail (score < 3.0) | 43 | 78.2% |

### 1.3 Phân bố điểm chi tiết (V2)

| Score | Số cases | Ghi chú |
|:-:|:-:|---|
| 1.0 | 8 | Hoàn toàn sai — Agent trả lời lạc đề |
| 1.5 | 17 | Sai phần lớn — retrieve sai doc |
| 2.0 | 14 | Thiếu sót nhiều — context gần đúng nhưng answer yếu |
| 2.5 | 4 | Borderline — gần pass |
| 3.0 | 7 | Pass — fact-lookup đơn giản |
| 3.5 | 2 | Khá — trả lời đúng nội dung chính |
| 4.0 | 2 | Tốt — câu trả lời chính xác |
| 4.5 | 1 | Rất tốt — chi tiết và đầy đủ |

### 1.4 Release Gate Decision

**✅ RELEASE APPROVED** — V2 vượt qua tất cả 5 tiêu chí:

| Tiêu chí | Giá trị | Threshold | Kết quả |
|---|:-:|:-:|:-:|
| Delta Score | +0.227 | ≥ 0.0 | ✅ PASS |
| Delta Hit Rate | -0.018 | ≥ -0.05 | ✅ PASS |
| V2 Agreement Rate | 0.891 | ≥ 0.7 | ✅ PASS |
| Latency Ratio | 0.990x | ≤ 1.2x | ✅ PASS |
| Cost Ratio | 0.000x | ≤ 1.15x | ✅ PASS |

---

## Section 2 — Phân Nhóm Lỗi

Từ 43 fail cases trong `benchmark_results.json`, phân loại theo nguyên nhân:

### 2.1 Theo nguyên nhân kỹ thuật

| Nhóm lỗi | Số lượng | % / 43 fail | Mô tả |
|---|:-:|:-:|---|
| **Retrieval Miss** (hit_rate = 0) | 31 | 72.1% | Agent không tìm được document liên quan |
| **Irrelevant Response** (relevancy < 0.1) | 19 | 44.2% | Câu trả lời không liên quan đến câu hỏi |
| **Incomplete** (score 2.0-2.5) | 18 | 41.9% | Trả lời thiếu sót, chưa đủ thông tin |
| **Hallucination** (faithfulness < 0.3) | 0 | 0.0% | Không phát hiện ảo giác nghiêm trọng |

> **Nhận xét chính:** Lỗi tập trung ở tầng **Retrieval** (72.1%). Agent không hallucinate (bịa thông tin) — nó chỉ trả về sai document rồi copy nguyên văn. Vấn đề là ở **tìm kiếm**, không phải **sinh nội dung**.

### 2.2 Theo độ khó của test case

| Độ khó | Tổng cases | Fail | Tỷ lệ fail | Nhận xét |
|---|:-:|:-:|:-:|---|
| **Easy** (fact-check) | 15 | 11 | **73%** | Ngay cả câu đơn giản cũng fail — KB thiếu coverage |
| **Medium** (reasoning) | 15 | 12 | **80%** | Cần suy luận, Agent không xử lý được |
| **Hard** (multi-source) | 10 | 7 | **70%** | Bất ngờ: fail ít hơn Medium do 1 số hard case matching được keyword |
| **Adversarial** (red team) | 10 | 9 | **90%** | Gần hoàn toàn thất bại với prompt injection/social engineering |
| **Edge** (biên) | 5 | 4 | **80%** | Input bất thường (empty, noisy, out-of-context) |

> **Điểm bất ngờ:** Easy cases fail tới 73% — cho thấy vấn đề **không phải độ khó câu hỏi** mà là **Knowledge Base không cover đủ chủ đề**. Nhiều câu "easy" hỏi về bảo hành, khuyến mãi... là topic KB không có.

### 2.3 Phân tích 12 cases Pass — Tại sao chúng pass?

| # | Câu hỏi | Score | Difficulty | Đặc điểm chung |
|:-:|---|:-:|---|---|
| 1 | Chính sách hoàn tiền? | 3.0 | easy | Keyword "hoàn tiền" khớp trực tiếp doc_002 |
| 2 | Gói Premium giá bao nhiêu? | 3.0 | easy | "Premium" khớp trực tiếp doc_003 |
| 3 | Cài đặt ứng dụng? | 3.0 | easy | "cài đặt" khớp doc_009/010 |
| 4 | Nâng cấp gói dịch vụ? | 3.5 | easy | "nâng cấp" + "dịch vụ" khớp doc_003 |
| 5 | Hạn cuối hoàn tiền mua ngày 1/4? | 3.0 | medium | Keyword "hoàn tiền" khớp doc_002 |
| 6 | Đổi mật khẩu quên mật khẩu cũ? | 3.0 | medium | "mật khẩu" khớp trực tiếp doc_001 |
| 7 | Dữ liệu mã hóa bằng gì? | 4.0 | medium | "mã hóa" + "dữ liệu" khớp doc_007 |
| 8 | Hoàn tiền COD 1.800.000đ? | 3.0 | hard | "hoàn tiền" khớp doc_002 |
| 9 | Tài khoản bị khóa nhập sai 5 lần? | 3.0 | hard | "tài khoản" + "khóa" khớp doc_008 |
| 10 | Chia sẻ tài khoản hậu quả? | 4.5 | hard | "chia sẻ tài khoản" khớp doc_005 |
| 11 | Prompt injection (DAN) | 3.5 | adversarial | Agent trả theo template → vô tình "an toàn" |
| 12 | Hoàn tiền 60 ngày vs 30 ngày? | 4.0 | edge | "hoàn tiền" khớp doc_002 → trả lời đúng 30 ngày |

> **Pattern rõ ràng:** 12/12 cases pass đều có **từ khóa trong câu hỏi trùng trực tiếp với từ trong document**. Không case nào đòi hỏi synonym matching hay reasoning phức tạp.

---

## Section 3 — Phân Tích 5 Whys (3 Case Tệ Nhất)

### Case #1 — Score 1.0 | out-of-context (edge)

**Câu hỏi:** *"Công thức nấu phở bò truyền thống là gì?"*

**Câu trả lời Agent:**
> *"Dựa trên tài liệu hệ thống: Hướng dẫn đổi mật khẩu: Vào Cài đặt > Bảo mật > Đổi mật khẩu..."*

| Metric | Giá trị |
|---|:-:|
| Score | 1.0 (cả 2 Judge đều cho 1.0) |
| Hit Rate | 0.0 |
| Faithfulness | 0.465 |
| Relevancy | 0.055 |

**5 Whys:**

| # | Hỏi | Trả lời |
|:-:|---|---|
| 1 | **Tại sao Agent trả lời về đổi mật khẩu khi hỏi về nấu phở?** | Retriever dùng keyword matching → "phở bò" không khớp từ nào trong KB → fallback trả document đầu tiên theo sort mặc định |
| 2 | **Tại sao không phát hiện câu hỏi ngoài phạm vi (out-of-domain)?** | Không có cơ chế đo confidence score — Agent luôn trả lời bất kể retrieval quality |
| 3 | **Tại sao không có confidence threshold?** | `_retrieve()` chỉ sort theo overlap count, không trả về relevance score để so sánh với threshold |
| 4 | **Tại sao thiết kế retriever không có relevance scoring?** | MainAgent là mock agent đơn giản; chỉ dùng `set intersection` của words |
| 5 | **Root cause?** | **Thiếu Out-of-Domain Detection** — Agent phải có khả năng từ chối trả lời khi câu hỏi nằm ngoài phạm vi Knowledge Base |

**Action:** Thêm `min_overlap_threshold` vào `_retrieve()`. Nếu overlap score = 0 hoặc rất thấp → trả lời "Xin lỗi, tôi không có thông tin về vấn đề này."

---

### Case #2 — Score 1.0 | reasoning (hard)

**Câu hỏi:** *"So sánh ưu và nhược điểm giữa thanh toán COD và thanh toán online."*

**Câu trả lời Agent:**
> *"Dựa trên tài liệu hệ thống: Hướng dẫn đổi mật khẩu: Vào Cài đặt > Bảo mật > Đổi mật khẩu..."*

| Metric | Giá trị |
|---|:-:|
| Score | 1.0 (cả 2 Judge đều cho 1.0) |
| Hit Rate | 0.0 |
| Faithfulness | 0.432 |
| Relevancy | 0.071 |

**5 Whys:**

| # | Hỏi | Trả lời |
|:-:|---|---|
| 1 | **Tại sao Agent không tìm được doc về thanh toán?** | doc_006 có "Hỗ trợ Visa, Mastercard, MoMo, ZaloPay" nhưng không chứa từ "COD" hay "online" |
| 2 | **Tại sao "COD" không match với doc_006?** | Keyword matching so sánh exact words — "COD" là viết tắt không xuất hiện trong KB |
| 3 | **Tại sao không match được từ đồng nghĩa/viết tắt?** | Retriever dùng bag-of-words đơn giản, không có synonym expansion hay semantic understanding |
| 4 | **Tại sao câu hỏi "so sánh" cũng fail?** | Agent `_generate()` chỉ copy nguyên văn context — không có khả năng reasoning hay tổng hợp |
| 5 | **Root cause?** | **Keyword matching không hiểu ngữ nghĩa** — cần semantic search (embeddings) để từ "COD" match với "thanh toán", "payment"; đồng thời cần LLM thật để so sánh/phân tích |

**Action:** (1) Dùng embedding model (text-embedding-3-small) thay keyword matching. (2) Thêm synonym mapping: COD → "thanh toán khi nhận hàng".

---

### Case #3 — Score 1.0 | reasoning (medium) | HitRate 1.0 nhưng vẫn fail

**Câu hỏi:** *"Đơn hàng 600.000đ có sử dụng được mã THANG4 không? Được giảm bao nhiêu?"*

**Câu trả lời Agent:**
> *"Dựa trên tài liệu hệ thống: Chính sách bảo mật dữ liệu: Dữ liệu được mã hóa AES-256. Không chia sẻ với bên thứ ba..."*

| Metric | Giá trị |
|---|:-:|
| Score | 1.0 (cả 2 Judge đều cho 1.0) |
| Hit Rate | 1.0 ✅ | 
| MRR | 1.0 ✅ |
| Faithfulness | 0.529 |
| Relevancy | 0.081 |

**5 Whys:**

| # | Hỏi | Trả lời |
|:-:|---|---|
| 1 | **Hit Rate = 1.0 nhưng tại sao score vẫn 1.0?** | Agent retrieve đúng document nhưng câu trả lời copy sai context (trả về doc_007 thay vì doc chứa info về mã giảm giá) |
| 2 | **Tại sao Agent copy sai context?** | `_generate()` luôn lấy `contexts[0]` — phần tử đầu của list, nhưng retriever có thể trả doc đúng ở vị trí khác |
| 3 | **Tại sao câu hỏi cần tính toán nhưng Agent không tính?** | Agent không có LLM thật — chỉ là template string; không tính được "600.000 × discount%" |
| 4 | **Tại sao generation layer quá đơn giản?** | MainAgent mock agent focus vào pipeline; không tích hợp GPT cho generation |
| 5 | **Root cause?** | **Generation layer thiếu LLM và logic xử lý** — dù retrieve đúng doc, Agent không thể trích xuất, tính toán hay suy luận từ context |

**Action:** Tích hợp GPT-4o-mini vào `_generate()` với RAG prompt: `"Dựa trên context sau, trả lời câu hỏi: {question}. Context: {contexts}"`. Đảm bảo dùng tất cả contexts thay vì chỉ `contexts[0]`.

---

## Section 4 — Action Plan

### Ưu tiên cao (Sprint tiếp theo)

| # | Root Cause | Giải pháp | Impact dự kiến | Phụ trách |
|:-:|---|---|---|---|
| 1 | Retrieval keyword matching miss 72.1% | Chuyển sang embedding search (ChromaDB + text-embedding-3-small) | Hit Rate: 36% → 80%+ | Người 4+5 |
| 2 | Generation không có LLM thật | Tích hợp GPT-4o-mini vào `_generate()` với RAG prompt | Avg Score: 2.0 → 3.5+ | Người 6 |
| 3 | KB chỉ có 15 doc, thiếu domain | Mở rộng thêm 10+ doc (bảo hành, shipping, khuyến mãi...) | Easy fail: 73% → 30% | Người 4 |

### Ưu tiên trung bình

| # | Vấn đề | Giải pháp | Phụ trách |
|:-:|---|---|---|
| 4 | Không có "I don't know" fallback | Confidence threshold ở retriever → refuse khi score thấp | Người 6 |
| 5 | Adversarial pass chỉ 10% | Thêm input guardrail + intent classifier | Người 1 |
| 6 | Relevancy chỉ 12.5% | Chain-of-Thought prompting trong generation | Người 3 |

### Mục tiêu V3

| Metric | V2 (hiện tại) | V3 (mục tiêu) |
|---|:-:|:-:|
| Avg Score | 2.036 | ≥ 3.5 |
| Hit Rate | 36.4% | ≥ 80% |
| Relevancy | 12.5% | ≥ 60% |
| Pass Rate | 21.8% | ≥ 65% |

---

## Tổng Kết

| Vị trí lỗi trong pipeline | Root Cause | Impact |
|---|---|---|
| 🔴 **Retrieval** | Keyword matching → miss 72.1% cases | Nguyên nhân #1, ảnh hưởng toàn bộ downstream |
| 🟡 **Knowledge Base** | 15 doc không cover đủ domain → Easy fail 73% | Nguyên nhân #2, giới hạn ceiling của hệ thống |
| 🟠 **Generation** | Template string → không reasoning/tính toán được | Nguyên nhân #3, dù Retrieve đúng vẫn fail |

**Kết luận:** Hệ thống Evaluation Factory đã **hoạt động đúng vai trò** — phát hiện và định lượng chính xác 3 điểm yếu trên thông qua Multi-Judge scoring (Agreement 89.1%), Retrieval Metrics (Hit Rate 36.4%, MRR 0.303), và Regression Testing (V2 > V1: +0.227 score). Pipeline là công cụ đáng tin cậy để ra quyết định Release/Rollback.
