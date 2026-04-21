# Reflection Cá Nhân - Nguyễn Thùy Linh

## 1. Thông tin cá nhân

| Trường | Giá trị |
| --- | --- |
| Họ tên | Nguyễn Thùy Linh |
| Mã sinh viên | 2A202600407 |
| Nhóm phụ trách | Người 2 - Bước 5: Async Runner |
| Ngày viết | 21/4/2026 |

## 2. Đóng góp cụ thể

Tôi phụ trách đúng phần Bước 5 trong walkthrough: triển khai Async Runner cho pipeline benchmark ở file [engine/runner.py](../../engine/runner.py). Mục tiêu của phần này là làm cho toàn bộ quá trình chạy test case diễn ra song song theo batch, đo được hiệu năng thực tế và tạo ra báo cáo tổng hợp đủ thông tin để nhóm có thể đánh giá tốc độ, độ ổn định và chi phí của hệ thống.

Những việc tôi đã làm trong phạm vi của mình:

- Thiết kế lại `BenchmarkRunner` để chạy test case theo batch bằng `asyncio.gather`, thay vì chạy tuần tự.
- Giữ nguyên luồng tích hợp cơ bản: gọi Agent, gọi Evaluator, rồi gọi Judge cho từng test case.
- Đo thời gian thực thi từng test case bằng `time.perf_counter()` để lấy latency chính xác hơn `time.time()`.
- Tích hợp hàm tổng hợp báo cáo hiệu năng `get_performance_report()` để xuất ra các chỉ số như latency trung bình, p50, p95, throughput.
- Cộng gộp token usage và cost usage từ kết quả trả về của Agent/Judge, nhưng vẫn giữ cơ chế fallback về 0 nếu metadata chưa có.
- Lưu `last_run_summary` để lần chạy gần nhất có thể được truy xuất lại mà không phải tính lại.
- Kiểm tra nhanh bằng smoke test với các stub tối giản để xác nhận runner hoạt động đúng và không làm vỡ interface cũ.

Điểm tôi chú ý nhất là không thay đổi cấu trúc trả về cốt lõi của mỗi test case, vì các phần khác của hệ thống vẫn cần đọc đúng các khóa `ragas`, `judge`, `status`. Nói cách khác, tôi chỉ mở rộng output theo hướng bổ sung thông tin hiệu năng, không phá vỡ dữ liệu đầu ra mà pipeline đang phụ thuộc.

## 3. Kiến thức kỹ thuật tôi nắm được

### Async Runner

Async Runner không chỉ là “chạy cho nhanh”, mà là cách tổ chức công việc để các lời gọi I/O-bound không chờ nhau một cách lãng phí. Trong bài này, Agent và Judge đều là những bước có độ trễ cao, nên việc gom thành batch và chạy song song bằng `asyncio.gather` giúp giảm đáng kể tổng thời gian benchmark.

Tôi hiểu rõ ba điểm quan trọng khi làm phần này:

1. `batch_size` là nút điều khiển cân bằng giữa tốc độ và an toàn.
2. Batch quá lớn có thể làm tăng rủi ro rate limit hoặc tạo spike tài nguyên.
3. Batch quá nhỏ thì mất lợi thế của async và throughput giảm.

### Latency, p50, p95 và throughput

- Latency là thời gian xử lý của từng test case.
- P50 cho biết mức thời gian điển hình của nửa số test case tốt hơn mức đó.
- P95 cho biết 95% test case chạy nhanh hơn ngưỡng đó, rất hữu ích để nhìn thấy các trường hợp chậm bất thường.
- Throughput cho biết hệ thống xử lý được bao nhiêu test case trên một giây, giúp đánh giá năng lực chạy benchmark ở quy mô lớn.

Trong thực tế, tôi không chỉ quan tâm trung bình. Nếu chỉ nhìn average thì một vài case rất chậm có thể bị che khuất. Vì vậy báo cáo có cả p50 và p95 để phản ánh đúng hành vi của runner trong điều kiện thật.

### Token usage và cost usage

Runner không tự sinh token, nhưng nó phải tổng hợp được token/cost từ các component được ghép vào pipeline. Tôi đã thiết kế phần tổng hợp theo hướng linh hoạt: nếu component nào trả về `tokens_used` hoặc `cost_usd` thì cộng vào báo cáo; nếu chưa có thì coi như 0 để không làm hỏng benchmark.

Điều này quan trọng vì cost là một phần của chất lượng sản phẩm. Một hệ thống chạy nhanh nhưng tốn quá nhiều token vẫn chưa phải là một hệ thống tốt. Tôi coi đây là phần bắt buộc của báo cáo hiệu năng, không phải phần phụ.

### Khái niệm liên quan để phối hợp pipeline

Dù tôi không trực tiếp implement các phần khác, tôi vẫn cần hiểu output của chúng để runner ghép đúng:

- Hit Rate và MRR là dữ liệu từ retrieval evaluator, runner phải truyền và tổng hợp đúng chứ không tự tính lại.
- Cohen’s Kappa là khái niệm liên quan đến độ đồng thuận giữa các judge, nên runner phải giữ được kết quả judge một cách ổn định để downstream có thể phân tích.
- Position Bias là một rủi ro ở lớp judge, vì vậy runner cần lưu kết quả đánh giá đủ rõ để nhóm khác có thể debug nếu sau này muốn kiểm tra bias.

## 4. Vấn đề tôi gặp và cách xử lý

### 1. Không được làm vỡ interface cũ

Khi bổ sung báo cáo hiệu năng, tôi phải giữ nguyên format kết quả mà các bước sau đang đọc. Nếu thêm trường mới nhưng đổi cấu trúc cũ, pipeline sẽ dễ lỗi dây chuyền.

**Cách xử lý:** chỉ mở rộng dict kết quả bằng các khóa mới như `token_usage`, `cost_usage`, `last_run_summary`, đồng thời giữ nguyên `test_case`, `agent_response`, `latency`, `ragas`, `judge`, `status`.

### 2. Xử lý trường hợp thiếu metadata

Không phải component nào cũng trả về đủ `tokens_used` hay `cost_usd`.

**Cách xử lý:** tôi cho runner fallback về 0 khi metadata thiếu, nhờ vậy benchmark vẫn chạy được ngay cả khi một component chưa hoàn thiện phần accounting.

### 3. Tính percentile mà không phụ thuộc thư viện ngoài

Tôi muốn báo cáo p50/p95 ổn định nhưng không muốn kéo thêm dependency không cần thiết.

**Cách xử lý:** tự viết hàm `_percentile()` dựa trên danh sách latency đã thu thập, đủ nhẹ và đủ chính xác cho mục tiêu báo cáo của lab.

### 4. Đảm bảo báo cáo có ý nghĩa thực tế

Chỉ có async thôi chưa đủ. Nếu không có summary, nhóm sẽ khó chứng minh rằng runner thực sự nhanh và hiệu quả.

**Cách xử lý:** tôi thêm `get_performance_report()` để tạo một bản tổng hợp duy nhất cho mỗi lần benchmark, bao gồm latency, throughput, token và cost.

## 5. Bài học rút ra

- Một runner tốt không chỉ chạy được, mà còn phải đo được.
- Tối ưu tốc độ phải đi kèm khả năng quan sát hiệu năng.
- Thiết kế output ổn định quan trọng không kém việc tối ưu logic xử lý.
- Khi làm việc với async, cần kiểm soát batch size và dữ liệu báo cáo ngay từ đầu, nếu không sẽ rất khó đánh giá chất lượng hệ thống sau này.

## 6. Tự đánh giá cá nhân

Tôi đánh giá phần mình làm đạt yêu cầu của Bước 5 vì đã đáp ứng đủ hai mục tiêu cốt lõi: chạy song song theo batch và tạo báo cáo hiệu năng có thể dùng ngay trong benchmark. Nếu cần cải tiến thêm, hướng tiếp theo của tôi là chuẩn hóa format cost/token thống nhất hơn giữa Agent và Judge, để báo cáo sau này còn chi tiết hơn nhưng vẫn giữ được độ đơn giản khi sử dụng.

## 7. Kết luận

Phần tôi phụ trách là lớp chạy benchmark trung tâm. Tôi đã tập trung vào tốc độ, độ ổn định và khả năng đo lường. Với tôi, đây là điểm then chốt của Bước 5: không chỉ làm cho pipeline chạy nhanh hơn, mà còn làm cho kết quả chạy benchmark đủ rõ ràng để nhóm có thể đánh giá và so sánh một cách nghiêm túc.