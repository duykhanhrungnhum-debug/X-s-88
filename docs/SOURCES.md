# Nguồn dữ liệu Xoso88

## Minh Ngọc

- Website nguồn: https://www.minhngoc.net.vn/
- Vai trò: nguồn kết quả xổ số để adapter thử nghiệm parse dữ liệu kết quả.
- Phạm vi thu thập: chỉ các bảng kết quả xổ số và số giải.
- Không thu thập: quảng cáo, banner, tracking, hình ảnh quảng cáo hoặc nội dung không thuộc kết quả.
- Không bypass CAPTCHA, paywall, access control hoặc biện pháp chống bot.

### Trạng thái

Đã xác minh rằng trang công khai có các bảng kết quả theo ngày và theo miền/tỉnh. Adapter trong repository hiện mới là lớp chuẩn hóa domain; chưa tuyên bố collector HTTP production đã hoạt động.

### Quy tắc xuất bản

Dữ liệu chỉ được chuyển sang `PUBLISHED` sau khi parser và validator xác nhận cấu trúc hợp lệ. Mỗi bản ghi phải giữ source URL và thời điểm thu thập để truy xuất provenance.
