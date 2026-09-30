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
| **Định hướng** | Hiện đại, dễ dùng, an toàn mặc định (an toàn theo chuẩn OpenSSL). | Hướng tới cấp thấp (low-level), thay thế thư viện PyCrypto cũ. |
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

## 2. MỤC TIÊU THỰC HÀNH: THƯ VIỆN CRYPTOTOOLKIT
Trong phần thực hành tiếp theo, chúng ta sẽ xây dựng thư viện `CryptoToolkit` tích hợp các chức năng mật mã cốt lõi:
1. `encrypt_file_aes(filepath, password)`: Mã hóa tệp tin bằng thuật toán **AES-256-GCM** (kèm xác thực toàn vẹn dữ liệu).
2. `decrypt_file_aes(encrypted_file, password)`: Giải mã tệp tin đã mã hóa.
3. `generate_rsa_keypair(key_size)`: Tạo cặp khóa bất đối xứng RSA (Public/Private Key).
4. `sign_data_rsa(data, private_key)`: Tạo chữ ký số trên dữ liệu bằng RSA.
5. `verify_signature_rsa(data, signature, public_key)`: Kiểm tra tính hợp lệ của chữ ký số.
6. `hash_password_secure(password)`: Băm mật khẩu an toàn chuẩn **Argon2**.
