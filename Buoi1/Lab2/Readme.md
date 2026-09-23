# BÁO CÁO THỰC HÀNH LAB 2: BẢO MẬT TRƯỚC KHI COMMIT (GITSECURE HOOK)

## 1. Mục tiêu
Thiết kế và triển khai hệ thống Pre-commit hook mang tên **GitSecure** để tự động kiểm tra an toàn mã nguồn trước khi thực hiện `git commit`, ngăn chặn các rủi ro bảo mật lọt vào kho mã nguồn (repository).

## 2. Tính năng chính
1. **Quét thông tin nhạy cảm (Secret Scanning)**:
   - Sử dụng Regex phát hiện các chuỗi nhạy cảm: `apikey`, `secret`, `password`, `token`, và `AWS Key (AKIA/ASIA)`.
2. **Quét lỗ hổng mã nguồn tĩnh (SAST)**:
   - Tích hợp công cụ **Bandit** (`bandit -r .`) tự động phát hiện các lỗ hổng bảo mật cấp độ High trong mã nguồn Python.
3. **Kiểm tra quyền truy cập file (Permission Check)**:
   - Kiểm tra quyền ghi "world-writable" (`stat.S_IWOTH`), tương thích với hệ điều hành Windows.
4. **Ghi nhật ký phát hiện (Audit Logging)**:
   - Tự động ghi lại các vi phạm kèm thời gian chi tiết vào `gitsecure.log`.

## 3. Cấu trúc thư mục Lab 2
```text
Lab2/
├── Readme.md                       # Tài liệu hướng dẫn và báo cáo
├── requirements.txt                # Thư viện phụ thuộc (bandit)
├── .githooks/
│   └── pre-commit                  # Script Python kiểm tra bảo mật trước commit
└── pre-commit-hook-test/
    └── bad.py                      # File mẫu kiểm thử bắt lỗi password hardcode
```

## 4. Hướng dẫn kích hoạt và sử dụng
- Kích hoạt hook:
  ```powershell
  git config core.hooksPath Buoi1/Lab2/.githooks
  ```
- Cài đặt công cụ Bandit:
  ```powershell
  pip install -r requirements.txt
  ```
- Khi cố tình commit file có chứa thông tin nhạy cảm (như mật khẩu được gán cứng dạng chuỗi), GitSecure sẽ chặn lại:
  ```text
  COMMIT BLOCKED by GitSecure:
   - Sensitive info found in ...
  ```
