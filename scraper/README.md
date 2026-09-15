# Scraper

Scraper được thiết kế theo mô hình source adapter. Mỗi nguồn cung cấp một adapter riêng để:

1. Fetch trang dữ liệu theo chính sách truy cập của nguồn.
2. Loại bỏ phần không phải dữ liệu kết quả khỏi DOM trước khi parse.
3. Parse bảng giải thưởng thành `LotteryResult`.
4. Validate cấu trúc trước khi dữ liệu có thể được publish.

Không parse hoặc lưu nội dung quảng cáo/banner/tracking. Không vượt qua CAPTCHA, paywall, access control hoặc cơ chế chống bot.

Source adapter đầu tiên sẽ chỉ được đánh dấu live sau khi có kiểm thử thực tế và xác minh kết quả.
