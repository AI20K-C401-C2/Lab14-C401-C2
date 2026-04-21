# Reflection - Lê Đức Thanh - 2A202600093

## 1. Đóng góp cụ thể

- Module em làm là phần nâng cao của `engine/llm_judge.py`
- Em phụ trách vai trò Người 3 trong nhóm
- Công việc em đã làm:
  - Viết `Simulation Mode` bằng hàm `_simulate_score()`
  - Thêm fallback để khi thiếu API key hoặc lỗi API thì hệ thống vẫn chấm được
  - Viết `check_position_bias()` để kiểm tra judge có bị thiên vị vị trí hay không
- Số commit: cập nhật theo lịch sử git cá nhân
- Thời gian làm: khoảng 1 giờ

## 2. Kiến thức kỹ thuật

### MRR

MRR là chỉ số dùng để xem tài liệu đúng xuất hiện sớm hay muộn trong kết quả retrieval. Nếu tài liệu đúng ở top đầu thì MRR cao, còn ở dưới thì MRR thấp.

### Agreement Rate

Agreement Rate là mức độ đồng thuận giữa các judge. Nếu hai judge chấm gần giống nhau thì kết quả đáng tin hơn. Nếu chênh lệch nhiều thì cần thêm judge để xử lý.

### Position Bias

Position Bias là hiện tượng judge có thể thích câu trả lời đứng trước hoặc đứng sau chỉ vì vị trí hiển thị. Em kiểm tra bằng cách cho chấm theo thứ tự `A/B`, sau đó đảo thành `B/A`, rồi so sánh kết quả.

### Simulation Mode

Simulation Mode là chế độ giả lập khi chưa có API key hoặc gọi model bị lỗi. Thay vì gọi model thật, hệ thống sẽ chấm dựa trên độ giống giữa câu trả lời và ground truth. Cách này giúp test pipeline nhanh hơn.

## 3. Trade-off chi phí và chất lượng

Nếu dùng judge thật bằng API thì kết quả sẽ tốt hơn nhưng tốn chi phí và phụ thuộc mạng. Nếu dùng simulation mode thì rẻ và nhanh hơn, nhưng độ chính xác không bằng model thật. Theo em, simulation mode phù hợp để test trong lúc phát triển, còn benchmark chính nên dùng judge thật.

## 4. Bài học kinh nghiệm

Qua phần này em hiểu rằng hệ thống đánh giá cũng có thể bị lỗi hoặc bị lệch, nên không thể tin hoàn toàn vào một judge duy nhất. Em cũng học được rằng fallback rất quan trọng, vì khi thiếu API key thì simulation mode vẫn giúp nhóm tiếp tục làm việc. Ngoài ra, em thấy position bias là một lỗi nhỏ nhưng ảnh hưởng khá nhiều đến độ tin cậy của kết quả chấm.
