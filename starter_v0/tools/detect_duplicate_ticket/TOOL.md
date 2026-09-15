---
name: detect_duplicate_ticket
track: bonus
kind: read
provider: local_ticket_store
requires_env: []
inputs: [summary, asset_id, threshold, max_results]
outputs: [status, matches, total_matches, scanned_records, skipped_records, review_required]
side_effect: none
requires_confirmation: false
---
# detect_duplicate_ticket — Bonus tool phần E

Tìm ticket tương tự trong `starter_v0/tickets/*.json`, chỉ đọc nội bộ, không gọi mạng, không tạo/xóa/sửa ticket. Không nhận đường dẫn từ model. Bỏ qua symlink, JSON lỗi và file trên 64 KiB.

## Cách hoạt động

- Chỉ so sánh ticket cùng asset ID; asset rỗng chỉ khớp ticket không có asset.
- Chuẩn hóa chữ thường, dấu tiếng Việt và dấu câu.
- Điểm Jaccard = số từ chung / số từ trong hợp của hai tập từ.
- Ngưỡng mặc định 0.7; trả tối đa 5 kết quả, sắp theo điểm rồi ticket ID.
- Chỉ trả ID, điểm và loại khớp; không trả nội dung ticket hoặc đường dẫn.
- File thiếu/sai cấu trúc được đếm ở skipped_records. Không có thư mục ticket được xem là kho rỗng.

## Ví dụ gọi trực tiếp

Chạy trong `starter_v0`:

```powershell
.\.venv\Scripts\python.exe -c "from tools import TOOL_FUNCTIONS; print(TOOL_FUNCTIONS['detect_duplicate_ticket'](summary='VPN timeout', asset_id='LT-204'))"
```

Trong UI: “Chỉ kiểm tra ticket trùng cho LT-204 với nội dung VPN timeout; không tạo ticket.”

## Giới hạn

Đây là gợi ý trùng lặp dựa trên từ, không phải so sánh ngữ nghĩa. Câu phủ định, đồng nghĩa, nội dung rất ngắn và lỗi đã tái phát có thể gây nhầm. Không lọc theo thời gian/trạng thái vì kho ticket hiện tại không có vòng đời trạng thái. Chỉ chấp nhận ticket ID định dạng LAB-xxxxxxxx của tool hiện có. Kiểm tra không phải khóa chống tạo trùng đồng thời hay bằng chứng xác nhận; create_ticket vẫn cần guard riêng nếu muốn bảo đảm ở runtime.
