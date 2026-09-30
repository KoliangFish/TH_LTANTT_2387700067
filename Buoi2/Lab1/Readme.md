# BÁO CÁO THỰC HÀNH BUỔI 2 - LAB 1: MÃ HOÁ VÀ TRIỂN KHAI PKI

- **Môn học**: Thực hành Lập trình An ninh Thông tin (TH_LTANTT)
- **Sinh viên**: Đặng Hải Tiến - MSSV: 2387700067
- **Chủ đề**: Mật mã hiện đại và Thư viện mật mã CryptoToolkit

---

## 1. TỔNG QUAN LÝ THUYẾT

### 1.1. Mã hóa đối xứng và Mã hóa bất đối xứng
Mã hóa là quá trình chuyển đổi dữ liệu gốc (Plaintext) thành bản mã không đọc được (Ciphertext) để đảm bảo tính bảo mật.

| Tiêu chí | Mã hóa đối xứng (Symmetric) | Mã hóa bất đối xứng (Asymmetric) |
| :--- | :--- | :--- |
| **Số lượng khóa** | Dùng chung 1 khóa bí mật cho cả mã hóa & giải mã. | Dùng cặp khóa: Khóa công khai (Public Key) & Khóa riêng tư (Private Key). |
| **Ưu điểm** | Tốc độ xử lý rất nhanh, tối ưu cho dữ liệu lớn. | Không cần chia sẻ khóa bí mật, an toàn phân phối khóa. |
| **Nhược điểm** | Khó khăn trong việc chia sẻ và quản lý khóa an toàn. | Tốc độ tính toán chậm, tốn tài nguyên phần cứng hơn. |
| **Thuật toán phổ biến** | **AES**, DES, 3DES, Blowfish. | **RSA**, ECC (Elliptic Curve), ElGamal. |

---

### 1.2. So sánh PyCA Cryptography và PyCryptodome trong Python

| Đặc điểm | PyCA Cryptography | PyCryptodome |
| :--- | :--- | :--- |
| **Định hướng** | Hiện đại, dễ dùng, an toàn mặc định (tuân thủ OpenSSL). | Hướng tới cấp thấp (low-level), thay thế thư viện PyCrypto cũ. |
| **Mức độ trừu tượng** | Cung cấp Recipe cấp cao (`fernet`) và tầng Hazmat khi cần can thiệp sâu. | Can thiệp trực tiếp vào từng block cipher, padding, nonce, mode. |
| **Ứng dụng tối ưu** | Phù hợp cho dự án sản phẩm thực tế, tích hợp framework (Flask, Django). | Phù hợp nghiên cứu, học thuật, tùy biến sâu và demo thuật toán. |

---

### 1.3. Các hàm sinh khóa mật khẩu (Key Derivation Function - KDF)
KDF giúp chuyển đổi mật khẩu người dùng (thường ngắn, dễ đoán) thành khóa mật mã có độ ngẫu nhiên cao và độ dài chuẩn, đồng thời bổ sung **Salt** và **Work Factor/Iterations** để chống tấn công vét cạn (Brute-force / Rainbow Tables):

1. **PBKDF2**: Chuẩn hóa theo RFC 8018, dựa trên HMAC (thường là HMAC-SHA256). Phổ biến rộng rãi nhưng khả năng kháng tấn công phần cứng GPU/ASIC ở mức trung bình.
2. **Scrypt**: Thiết kế theo cơ chế Memory-hard (tiêu tốn bộ nhớ RAM song song với tính toán CPU), chống lại việc sử dụng chip chuyên dụng ASIC để phá khóa.
3. **Argon2**: Thuật toán chiến thắng cuộc thi *Password Hashing Competition (PHC 2015)*, là tiêu chuẩn bảo mật hiện đại nhất hiện nay.
   - **Argon2d**: Tối ưu chống tấn công GPU/ASIC (thích hợp cho tiền mã hóa).
   - **Argon2i**: Tối ưu chống tấn công kênh kề (Side-channel attacks).
   - **Argon2id**: Kết hợp cả hai cơ chế trên, được khuyến nghị sử dụng rộng rãi nhất.

---

### 1.4. Hàm băm mật mã và Chữ ký số

#### A. Hàm băm (Cryptographic Hash Function)
- Chuyển dữ liệu đầu vào kích thước tùy ý thành chuỗi digest có độ dài cố định.
- **Tính chất cốt lõi**:
  - *Tính một chiều (Pre-image resistance)*: Không thể đảo ngược từ chuỗi băm về dữ liệu gốc.
  - *Hiệu ứng tuyết lở (Avalanche effect)*: Thay đổi 1 bit đầu vào làm thay đổi toàn bộ chuỗi băm đầu ra.
  - *Kháng va chạm (Collision resistance)*: Bất khả thi để tìm hai dữ liệu đầu vào khác nhau có cùng chuỗi băm.
- Thuật toán tiêu chuẩn: **SHA-256**, **SHA-3** (các thuật toán cũ như MD5, SHA-1 đã bị phá vỡ và coi là lỗi thời).

#### B. Chữ ký số (Digital Signature)
- Phương thức bảo đảm tính toàn vẹn (Integrity), xác thực nguồn gốc (Authentication) và chống chối bỏ (Non-repudiation).
- **Quy trình hoạt động**:
  1. **Ký số**: Người gửi băm dữ liệu gốc và dùng **Private Key** của mình để mã hóa chuỗi băm đó tạo thành chữ ký số.
  2. **Xác minh**: Người nhận dùng **Public Key** của người gửi để giải mã chữ ký, lấy chuỗi băm ban đầu và so sánh với chuỗi băm của tài liệu nhận được.

---

## 2. CẤU TRÚC DỰ ÁN THỰC HÀNH: CRYPTO-TOOLKIT
```text
Buoi2/Lab1/crypto-toolkit/
├── files/
│   └── data.txt                    # Dữ liệu kiểm thử ("HUTECH University")
├── securecrypto/                   # Thư viện mật mã chính
│   ├── __init__.py                 # Khởi tạo package (__version__ = "0.1.0")
│   ├── aes_utils.py                # Mã hóa/giải mã AES-256-GCM & PBKDF2HMAC
│   ├── hash_utils.py               # Băm mật khẩu an toàn bằng Argon2
│   ├── rsa_utils.py                # Cặp khóa RSA, ký số & xác thực chữ ký
│   ├── cli.py                      # Giao diện dòng lệnh CLI (securecrypto-cli)
│   ├── api.py                      # REST API Flask (/encrypt, /decrypt)
│   └── app_gui.py                  # Giao diện đồ họa Tkinter (GUI)
├── tests/                          # Bộ kiểm thử tự động với Pytest
│   ├── test_aes_utils.py           # Test mã hóa/giải mã AES
│   ├── test_hash_utils.py          # Test băm và xác thực Argon2
│   └── test_rsa_utils.py           # Test sinh khóa, ký và xác thực RSA
├── requirements.txt                # Thư viện phụ thuộc
└── setup.py                        # Cấu hình cài đặt package & CLI entry-point
```

---

## 3. HƯỚNG DẪN CÀI ĐẶT & CHẠY KIỂM THỬ

### 3.1. Cài đặt package ở chế độ Editable
Di chuyển vào thư mục `Buoi2/Lab1/crypto-toolkit` và cài đặt:
```powershell
pip install -e .
```

### 3.2. Chạy bộ kiểm thử tự động (Unit Tests)
Chạy lệnh kiểm thử bằng `pytest`:
```powershell
pytest tests/
```
**Kết quả kiểm thử:**
```text
collected 6 items

tests\test_aes_utils.py .                                                [ 16%]
tests\test_hash_utils.py ..                                              [ 50%]
tests\test_rsa_utils.py ...                                              [100%]

============================== 6 passed in 0.71s ==============================
```
✅ **6/6 test cases đạt kết quả PASSED 100%.**

---

### 3.3. Kiểm thử qua Giao diện dòng lệnh (CLI)
1. **Mã hóa file**:
   ```powershell
   securecrypto-cli --encrypt .\files\data.txt --password pass123
   ```
   *Kết quả*: Hệ thống tạo file mã hóa `.\files\data.txt.enc` và in ra chuỗi khóa Base64.
2. **Giải mã file**:
   ```powershell
   securecrypto-cli --decrypt .\files\data.txt.enc --password [khoa_base64_o_buoc_tren]
   ```
   *Kết quả*: Hệ thống giải mã ra file `.\files\data.txt.dec` có nội dung chuẩn xác: `HUTECH University`.

---

### 3.4. Kiểm thử qua Giao diện đồ họa (GUI)
Khởi chạy ứng dụng Tkinter:
```powershell
python securecrypto/app_gui.py
```
- Nhập mật khẩu > Bấm **Encrypt** > Chọn file `data.txt` -> Nhận chuỗi Key.
- Dán Key vào ô mật khẩu > Bấm **Decrypt** > Chọn file `data.txt.enc` -> Nhận đường dẫn file đã giải mã `.dec`.

---

### 3.5. Kiểm thử qua Web REST API (Flask)
Khởi chạy máy chủ API:
```powershell
python securecrypto/api.py
```
Sử dụng Postman để kiểm tra:
1. **Endpoint Mã hóa (`POST http://127.0.0.1:5000/encrypt`)**:
   - Body > `form-data`:
     - `file`: chọn file `data.txt`
     - `password`: `pass123`
   - Nhận về JSON: `{"key": "..."}` và file đã mã hóa trong `securecrypto/upload/`.
2. **Endpoint Giải mã (`POST http://127.0.0.1:5000/decrypt`)**:
   - Body > `form-data`:
     - `file`: chọn file `data.txt.enc`
     - `password`: dán chuỗi `key` Base64 nhận được từ bước mã hóa.
   - Nhận về JSON: `{"output": "...\\data.txt.dec"}`.

---

### 3.6. Kiểm thử tương thích với GitSecure Pre-commit Hook (từ Buổi 1 - Lab 2)
- Khi lập trình viên vô tình cài cứng mật khẩu thực tế trong tệp kiểm thử `test_hash_utils.py`, hệ thống **GitSecure Pre-commit Hook** (đã xây dựng ở Buổi 1) lập tức phát hiện và chặn lại:
  ```text
  COMMIT BLOCKED by GitSecure:
   - Sensitive info found in crypto-toolkit/tests/test_hash_utils.py: pattern password\s*=\s*['\"][^'\"]{4,}['\"]
  ```
- Sau khi xử lý an toàn bằng cách loại bỏ mật khẩu hardcoded (`password = ""`), GitSecure cho phép thông qua:
  ```text
  GitSecure: All checks passed.
  ```
