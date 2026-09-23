# BÁO CÁO THỰC HÀNH LAB 3: GHI NHẬT KÝ ƯU TIÊN BẢO MẬT (SECURE LOGGER)

## 1. Mục tiêu
Xây dựng hệ thống ghi nhật ký an toàn (**SecureLogger**) tích hợp vào API Flask và thư viện **SecureValidator** từ Lab 1 nhằm phục vụ giám sát, kiểm toán và phát hiện bất thường mà không làm rò rỉ dữ liệu nhạy cảm.

## 2. Tính năng chính
1. **Đa cấp độ Log (Multi-level Logging)**:
   - Hỗ trợ các mức log tiêu chuẩn: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
2. **Che giấu thông tin định danh cá nhân (PII Masking)**:
   - Tự động nhận diện và ẩn giấu Email (`<email_masked>`) và các chuỗi Token/API Key/Password (`<token_masked>`) trong thông điệp và payload.
3. **Định dạng cấu trúc JSON (Structured JSON Logging)**:
   - Sử dụng `JSONFormatter` tùy biến để lưu log dưới định dạng JSON có cấu trúc (`timestamp`, `level`, `message`, `data`, `results`).
4. **Quản lý luân phiên và nén Log (Log Rotation & Compression)**:
   - Kế thừa `RotatingFileHandler` với kích thước tối đa `1MB` và lưu tối đa 2 bản sao lưu dự phòng.
   - Tự động nén các file log cũ sang định dạng `.gz` thông qua lớp `GZipRotator`.
5. **Chống thay đổi trái phép (Tamper Detection)**:
   - Mỗi dòng log ghi ra sẽ được tính toán mã băm mật mã **SHA-256** và lưu vết vào file chữ ký `secure.log.sig`.
   - Giúp kiểm toán viên đối chiếu và phát hiện nếu file nhật ký `secure.log` bị chỉnh sửa hoặc can thiệp trái phép.

## 3. Cấu trúc thư mục Lab 3
```text
Lab3/
├── Readme.md                       # Tài liệu hướng dẫn và giải thích tính năng
└── secure_logger_lab/
    ├── app.py                      # Flask API endpoint /validate
    ├── requirements.txt            # Thư viện Flask
    ├── securevalidator/            # Thư viện kiểm tra dữ liệu từ Lab 1
    │   ├── __init__.py
    │   └── core.py
    └── securelogger/               # Module ghi log bảo mật
        ├── __init__.py
        └── logger.py
```

## 4. Hướng dẫn chạy và kiểm thử

### Khởi động server
Tại thư mục `Buoi1/Lab3/secure_logger_lab`:
```powershell
python app.py
```

### Kiểm thử qua API (Postman / cURL)
- **Method**: `POST`
- **URL**: `http://localhost:5000/validate`
- **Headers**: `Content-Type: application/json`
- **Body (JSON)**:
```json
{
  "email": "phuoc@example.com",
  "url": "https://secure.com",
  "filename": "report.pdf",
  "sql": "' OR 1=1 --",
  "html": "<script>alert(1)</script>"
}
```

- **Kết quả trả về (JSON)**:
```json
{
  "email": true,
  "filename": true,
  "html": "&lt;script&gt;alert(1)&lt;/script&gt;",
  "sql": "1=1",
  "url": true
}
```

- **Kiểm tra file `secure.log`**:
```json
{"timestamp": "...", "level": "INFO", "message": "Validation check performed", "data": "{'email': '<email_masked>', 'url': 'https://secure.com', 'filename': 'report.pdf', 'sql': \"' OR 1=1 --\", 'html': '<script>alert(1)</script>'}", "results": "{'email': True, 'url': True, 'filename': True, 'sql': '1=1', 'html': '&lt;script&gt;alert(&quot;1&quot;)&lt;/script&gt;'}"}
```
Thông tin email nhạy cảm đã tự động được che giấu thành `<email_masked>`.

- **Kiểm tra file `secure.log.sig`**:
Chứa mã băm SHA-256 tương ứng của dòng log để phát hiện thay đổi trái phép.
