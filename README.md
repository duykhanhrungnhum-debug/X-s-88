# Xoso88

Website kết quả xổ số Việt Nam và hệ thống thu thập dữ liệu tự động.

## Mục tiêu
- Hiển thị kết quả xổ số theo tỉnh/khu vực và ngày.
- Thu thập dữ liệu từ các nguồn kết quả xổ số được cấu hình.
- Chỉ parse dữ liệu kết quả; không thu thập quảng cáo, banner hoặc tracking.
- Lưu nguồn, thời điểm lấy dữ liệu và trạng thái xác thực để truy xuất được provenance.
- Không công bố dữ liệu chưa qua kiểm tra hợp lệ.

## Kiến trúc ban đầu
- `backend/`: API và domain models.
- `scraper/`: collector và source adapters.
- `tests/`: kiểm thử parser/validator.
- `docs/`: thiết kế và chính sách nguồn dữ liệu.

## Nguyên tắc dữ liệu
Pipeline dự kiến: `FETCHED -> PARSED -> VALIDATED -> PUBLISHED`.

Bot không bypass CAPTCHA, paywall, access control hoặc biện pháp chống bot. Mỗi source adapter phải tuân thủ điều kiện truy cập áp dụng cho nguồn đó.

## Trạng thái
Khởi tạo project. Chưa tuyên bố website production hoặc nguồn dữ liệu live đã được tích hợp.
