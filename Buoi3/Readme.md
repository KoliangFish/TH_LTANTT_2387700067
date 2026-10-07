# BUỔI 3: BẢO MẬT MẠNG MÁY TÍNH

**Đặng Hải Tiến — MSSV 2387700067**
Nguồn yêu cầu: `lab-03.pdf` (giáo trình tham khảo, không kèm trong bài nộp), 29 trang.

Giáo trình có **2 bài thực hành**, tương ứng với hai thư mục:

| Bài | Nội dung giáo trình | Mã nguồn | Hướng dẫn và ảnh case |
| --- | --- | --- | --- |
| Lab1 | 3.2 SecureChat, trang 3–14 | `Lab1/secure-chat/` | [Lab1/Readme.md](Lab1/Readme.md) |
| Lab2 | 3.4 NetRecon, trang 15–29 | `Lab2/netrecon/` | [Lab2/Readme.md](Lab2/Readme.md) |

## Chuẩn bị một lần

Mở PowerShell tại thư mục gốc repository. Các lệnh dưới đây dùng Python 3.10 trở lên:

```powershell
python -m venv Buoi3/.venv
& .\Buoi3\.venv\Scripts\Activate.ps1
python -m pip install -r Buoi3/Lab1/secure-chat/requirements.txt
python -m pip install -r Buoi3/Lab2/netrecon/requirements.txt
python -m pip install -r Buoi3/requirements-dev.txt
```

Nếu PowerShell chặn Activate.ps1, có thể dùng trực tiếp Python của môi trường:

```powershell
.\Buoi3\.venv\Scripts\python.exe -m pip install -r Buoi3/Lab1/secure-chat/requirements.txt
```

Trong mỗi terminal mới, kích hoạt lại môi trường. Xem README từng Lab để chạy các ứng dụng và làm lại các case theo thứ tự.

## Kiểm tra và tạo lại ảnh báo cáo

```powershell
Push-Location Buoi3/Lab1/secure-chat
python -m pytest -q
python demo.py
Pop-Location
Push-Location Buoi3/Lab2/netrecon
python -m pytest -q
python demo.py
python capture_web.py
Pop-Location
```

`demo.py` dùng socket/TLS/HTTP/SMTP cục bộ thật, có assertion kiểm tra kết quả. Các ảnh CLI được render từ kết quả chạy, kèm tệp `.txt` đối chiếu; chúng **không phải ảnh chụp cửa sổ terminal**. `capture_web.py` chụp giao diện bằng Chrome headless thật, cần Chrome và Playwright. Có thể tự chụp terminal khi làm bài nếu giảng viên yêu cầu ảnh màn hình desktop.

## Kết quả đã kiểm tra

- Lab1: 4 unit test và 6 nhóm case tích hợp TLS/E2EE/phòng chat.
- Lab2: 11 unit test và 6 nhóm case tích hợp CLI/TCP/UDP/banner/policy/web/email/log.
- Web: ảnh trang nhập, trang kết quả, lỗi nhập liệu; kiểm tra chiều rộng trên mobile.
- Email: kiểm chứng SMTP cục bộ và gửi/nhận Gmail thật, có ảnh minh chứng trong README Lab2.
- Nmap: có tích hợp `-sV`, `-sS`, `-sU`; máy hiện tại chưa có Nmap/Npcap nên chưa chạy tích hợp Nmap thật.

Khóa/chứng chỉ, `.env` và log lúc chạy đã được loại khỏi Git bằng `Buoi3/.gitignore`. Không gửi `room_keys.json`, khóa riêng hay mật khẩu ứng dụng lên GitHub.

## Đưa bài lên GitHub sau khi tự kiểm tra

Chạy tại gốc repository:

```powershell
git status --short
git add Buoi3
git diff --cached --stat
git commit -m "Add Buoi3 SecureChat and NetRecon labs"
git push
```

Chỉ stage `Buoi3` để không gom các thay đổi khác đang có trong repository. Bài nộp không kèm file giáo trình. Bài gồm mã nguồn và báo cáo ảnh thực hành thủ công của Lab1, Lab2; dùng các lệnh trên khi cập nhật bài sau này.
