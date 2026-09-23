# BÁO CÁO THỰC HÀNH LAB 1: SECURE VALIDATOR & SANITIZER

---

## 1. TỔNG QUAN VÀ TÓM TẮT TÍNH NĂNG CỦA BÀI LAB

Bài thực hành **SecureValidator** hướng dẫn xây dựng một thư viện Python (`securevalidator`) và ứng dụng Web (Flask) nhằm thực hiện hai cơ chế cốt lõi trong an toàn bảo mật ứng dụng web: **Kiểm tra tính hợp lệ dữ liệu (Input Validation)** và **Làm sạch dữ liệu (Sanitization)** theo tiêu chuẩn phòng chống các lỗ hổng phổ biến của OWASP (Top 10).

### Cấu trúc dự án
```text
Lab1/
├── Readme.md
└── secure-validator-lab/
    ├── app.py                      # Ứng dụng web Flask xử lý form và hiển thị kết quả
    ├── requirements.txt            # Danh sách thư viện phụ thuộc (Flask, Gunicorn)
    ├── securevalidator/
    │   ├── __init__.py             # Module export các hàm xác thực và làm sạch
    │   └── core.py                 # Mã nguồn logic xử lý chính
    ├── templates/
    │   └── index.html              # Giao diện web người dùng (sử dụng Pico.css)
    └── tests/
        └── test_validators.py      # Bộ kiểm thử Unit Test tự động (10 test cases)
```

### Các tính năng bảo mật chính đã cài đặt:
1. **Xác thực định dạng Email (`validate_email`)**:
   - Sử dụng biểu thức chính quy (Regex) theo nguyên tắc **Whitelist** để kiểm tra cấu trúc email chuẩn `username@domain.tld`.
   - Ngăn chặn nhập các ký tự đặc biệt nguy hiểm hoặc chuỗi định dạng sai lệch.

2. **Xác thực URL và phòng chống SSRF (`validate_url`)**:
   - Sử dụng thư viện `urllib.parse` để phân tách và phân tích các thành phần của URL.
   - Whitelist giao thức an toàn: Chỉ chấp nhận giao thức `http` và `https`.
   - Bắt buộc phải có `netloc` (địa chỉ host/tên miền hợp lệ).
   - Ngăn chặn các scheme nguy hiểm thường dùng trong tấn công Server-Side Request Forgery (SSRF) hoặc Local File Inclusion (LFI) như `file://`, `ftp://`, `gopher://`, `dict://`, `javascript:`, `data:`.

3. **Xác thực tên file và phòng chống Path Traversal (`validate_filename`)**:
   - Ngăn chặn tấn công duyệt thư mục (Directory / Path Traversal) để đọc trộm file nhạy cảm của hệ thống (ví dụ: `../../etc/passwd` hay `..\Windows\System32`).
   - Kiểm tra và từ chối các ký tự điều hướng: chuỗi hai dấu chấm `..`, dấu gạch chéo `/`, và dấu gạch chéo ngược `\`.
   - Đảm bảo tính an toàn bằng cách so sánh `os.path.basename(filename) == filename` (chỉ chấp nhận tên file đơn thuần, không chứa đường dẫn).

4. **Làm sạch chuỗi SQL chống SQL Injection (`sanitize_sql_input`)**:
   - Áp dụng kỹ thuật lọc Blacklist các ký tự điều khiển cú pháp SQL nguy hiểm: `'`, `"`, `;`, `--`, `#`.
   - Loại bỏ các từ khóa truy vấn SQL nguy hiểm (không phân biệt chữ hoa, chữ thường): `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `UNION`, `WHERE`, `OR`, `AND`.
   - Ngăn chặn các chuỗi khai thác SQLi kinh điển như `' OR 1=1 --`.

5. **Làm sạch chuỗi HTML chống Cross-Site Scripting - XSS (`sanitize_html_input`)**:
   - Sử dụng hàm chuẩn an toàn `html.escape()`.
   - Chuyển đổi các ký tự nguy hiểm có thể kích hoạt mã JavaScript trong ngữ cảnh HTML (`<`, `>`, `&`, `"`, `'`) thành các thực thể HTML (HTML Entities: `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&#x27;`).
   - Ngăn chặn trình duyệt thực thi các thẻ kịch bản độc hại như `<script>alert('XSS')</script>`.

6. **Giao diện Web tương tác trực quan (`app.py` & `index.html`)**:
   - Xây dựng giao diện web nhẹ nhàng, hiện đại bằng **Pico.css**.
   - Cho phép người dùng trực tiếp nhập thử nghiệm các vector tấn công và quan sát kết quả kiểm tra/làm sạch theo thời gian thực (đánh dấu trực quan màu xanh khi Hợp lệ, màu đỏ khi Không hợp lệ).

7. **Kiểm thử tự động bằng Unit Test (`tests/test_validators.py`)**:
   - Xây dựng 10 test case kiểm thử toàn diện cho các trường hợp dữ liệu hợp lệ và dữ liệu độc hại/tấn công cho cả 5 chức năng bảo mật.
   - Chạy kiểm thử tự động đạt 100% kết quả thành công (`OK`).

---

## 2. CHI TIẾT VỀ WHITELIST VÀ BLACKLIST TRONG PHẦN ĐIỀN GMAIL / EMAIL

Trong an toàn thông tin và lập trình phòng thủ (Defensive Programming), **Whitelist (Danh sách cho phép / Allowlist)** và **Blacklist (Danh sách chặn / Blocklist)** là hai triết lý tiếp cận căn bản để kiểm soát dữ liệu đầu vào.

### A. Phân tích Whitelist trong bài Lab hiện tại

Trong hàm `validate_email(email: str)` của bài lab:
```python
def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.fullmatch(pattern, email) is not None
```

#### Cách hoạt động theo cơ chế Whitelist:
Bản chất của biểu thức chính quy trên là một **Whitelist ký tự và cấu trúc**:
- Ký tự bắt đầu `^` và kết thúc `$`: Sử dụng cùng với `re.fullmatch()` đảm bảo toàn bộ chuỗi phải khớp hoàn toàn từ đầu đến cuối, không cho phép chèn ký tự lạ ở phía trước hoặc phía sau.
- **Whitelist cho phần tên người dùng (Username - trước dấu `@`)**:
  - Biểu thức: `[\w\.-]+`
  - Các ký tự duy nhất được phép (Whitelist):
    + `\w`: Chữ cái thường (`a-z`), chữ cái hoa (`A-Z`), chữ số (`0-9`), và dấu gạch dưới `_`.
    + `\.`: Dấu chấm `.`.
    + `-`: Dấu gạch ngang `-`.
  - Mọi ký tự khác nằm ngoài danh sách trên (như khoảng trắng, dấu phẩy, dấu nháy đơn `'`, dấu nháy kép `"`, dấu ngoặc nhọn `< >`, dấu chấm phẩy `;`, ký tự xuống dòng `\n`, `\r`, v.v.) đều bị **từ chối ngay lập tức**.
- **Whitelist ký tự phân cách**: Bắt buộc phải có đúng **một ký tự `@`** ngăn cách giữa Username và Domain.
- **Whitelist cho phần tên miền (Domain Name)**:
  - Biểu thức: `[\w\.-]+`
  - Chỉ cho phép các chữ cái, chữ số, dấu gạch dưới, gạch ngang và dấu chấm.
- **Whitelist cho phần tên miền cấp cao nhất (Top-Level Domain - TLD)**:
  - Biểu thức: `\.\w+$`
  - Bắt buộc phải có dấu chấm `.` và theo sau bởi một hoặc nhiều ký tự chữ/số.

---

### B. Áp dụng Whitelist cụ thể cho dịch vụ Gmail

Nếu bài toán nâng cấp lên yêu cầu **chỉ cho phép nhập tài khoản Gmail hợp lệ**, ta áp dụng Whitelist ở hai cấp độ:

#### 1. Whitelist về Tên miền (Domain Whitelist)
Thay vì chấp nhận mọi đuôi tên miền, hệ thống chỉ đưa `@gmail.com` (và có thể là `@googlemail.com`) vào Whitelist:
```python
# Chỉ cho phép tên miền thuộc Whitelist của Google Gmail
GMAIL_WHITELIST_PATTERN = r'^[a-zA-Z0-9.]+@gmail\.com$'
```
- Bất kỳ email có đuôi khác như `@yahoo.com`, `@outlook.com`, hoặc các tên miền độc hại đều bị từ chối mặc định (**Default Deny**).

#### 2. Whitelist theo quy tắc đặt tên người dùng của Google Gmail
Google áp dụng các quy chuẩn Whitelist nghiêm ngặt cho username:
- **Độ dài hợp lệ (Length Whitelist)**: Từ 6 đến 30 ký tự.
- **Tập ký tự cho phép (Character Whitelist)**: Chỉ bao gồm chữ cái (`a-z`, không phân biệt hoa thường), chữ số (`0-9`), và dấu chấm (`.`).
- **Quy tắc dấu chấm (Position Whitelist)**:
  - Dấu chấm không được nằm ở đầu hoặc cuối username.
  - Không được có hai hay nhiều dấu chấm liên tiếp (`..`).

---

### C. Phân tích Blacklist trong bài toán xác thực Email / Gmail

**Blacklist (Chặn cụ thể)** là kỹ thuật định nghĩa trước các mẫu, từ khóa hoặc giá trị độc hại đã biết để loại bỏ hoặc ngăn chặn.

Trong phần điền Email/Gmail, cơ chế Blacklist thường được triển khai cho các mục đích:

1. **Blacklist các tên miền Email rác / Email dùng một lần (Disposable / Temporary Email Domains)**:
   - Kẻ tấn công hoặc người dùng ảo thường sử dụng các dịch vụ email tạm thời 10 phút để vượt qua bước kích hoạt tài khoản hoặc spam hệ thống.
   - Danh sách Blacklist tên miền:
     ```python
     DISPOSABLE_DOMAIN_BLACKLIST = {
         "tempmail.com", "10minutemail.com", "guerrillamail.com",
         "mailinator.com", "throwawaymail.com", "yopmail.com"
     }
     ```
   - Khi người dùng nhập email có domain nằm trong danh sách đen trên, hệ thống sẽ từ chối.

2. **Blacklist các ký tự nguy hiểm đặc thù (Anti-Injection Blacklist)**:
   - **Ký tự ngắt dòng (CRLF Injection / SMTP Header Injection)**: Ký tự `\r` (CR) và `\n` (LF) trong email có thể bị kẻ tấn công lợi dụng để chèn thêm các header SMTP độc hại (như `Bcc:`, `Cc:`, `Subject:`) nhằm biến máy chủ gửi mail của hệ thống thành công cụ phát tán thư rác.
   - **Null Byte Injection (`\0` hay `%00`)**: Dùng để cắt chuỗi trong các ngôn ngữ tầng dưới (C/C++).
   - **Ký tự trích dẫn nguy hiểm (`"`, `'`, `\`, `;`)**: Ngăn chặn chuỗi khai thác SQLi hoặc Command Injection ẩn trong trường email.

3. **Blacklist các tên tài khoản hệ thống / tài khoản đặc quyền (Reserved Names Blacklist)**:
   - Ngăn chặn người dùng đăng ký hoặc giả mạo các email quản trị viên:
     ```python
     RESERVED_USERNAME_BLACKLIST = {
         "admin", "administrator", "root", "support",
         "security", "postmaster", "hostmaster", "abuse"
     }
     ```

---

### D. So sánh Whitelist và Blacklist trong xác thực Email

| Tiêu chí | Whitelist (Danh sách cho phép) | Blacklist (Danh sách chặn) |
| :--- | :--- | :--- |
| **Triết lý thiết kế** | **Từ chối mặc định (Default Deny)**: Chỉ cho phép những gì đã được định nghĩa là an toàn. | **Cho phép mặc định (Default Allow)**: Cho phép tất cả, chỉ chặn những gì được coi là xấu. |
| **Độ an toàn** | **Rất cao**. Phòng ngừa được cả các lỗ hổng chưa biết (Zero-day) và các ký tự dị biệt. | **Thấp hơn**. Rất dễ bị kẻ tấn công vượt qua (Bypass) bằng các biến thể mã hóa, Unicode, hoặc trường hợp ngoại lệ chưa kịp cập nhật. |
| **Bảo trì** | Ổn định, ít khi phải sửa đổi quy tắc nếu định dạng nghiệp vụ không đổi. | Cần cập nhật liên tục khi xuất hiện các kỹ thuật tấn công hoặc dịch vụ email rác mới. |
| **Ứng dụng tốt nhất** | Kiểm tra định dạng cấu trúc cú pháp email, tập ký tự cho phép của username, và danh sách domain tổ chức cho phép. | Chặn các domain email tạm thời (disposable mail), chặn email nằm trong danh sách đen phát tán mã độc / spam đã xác định. |

> **Khuyến nghị an toàn theo chuẩn OWASP:**
> Luôn ưu tiên áp dụng **Whitelist** ở bước kiểm tra cú pháp và định dạng (như hàm `validate_email` bằng Regex). Cơ chế **Blacklist** chỉ nên dùng như một lớp phòng thủ chiều sâu thứ hai (Defense-in-depth) để lọc thêm danh sách spam/disposable domain đã biết.

---

## 3. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY THỬ NGHIỆM

### Cài đặt môi trường
1. Di chuyển vào thư mục dự án:
   ```bash
   cd secure-validator-lab
   ```
2. Cài đặt các gói phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

### Chạy kiểm thử tự động (Unit Test)
Chạy bộ test cases có sẵn để xác thực độ chính xác của các bộ lọc:
```bash
python -m unittest discover tests
```
*Kết quả mong đợi:*
```text
Ran 10 tests in 0.001s
OK
```

### Khởi chạy ứng dụng Web Flask
Khởi động máy chủ phát triển:
```bash
python app.py
```
Truy cập vào trình duyệt web tại địa chỉ: `http://127.0.0.1:5000` để thử nghiệm các tính năng trên giao diện đồ họa.
