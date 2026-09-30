import tkinter as tk
from tkinter import filedialog, messagebox
from securecrypto import aes_utils

def encrypt():
    file = filedialog.askopenfilename(title="Chọn file cần mã hóa (VD: data.txt)")
    if not file:
        return
    pw = password_entry.get().strip()
    if not pw:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập mật khẩu vào ô trên trước khi Encrypt!")
        return
    try:
        key = aes_utils.encrypt_file_aes(file, pw)
        result_label.config(text=f"Key: {key}", fg="black")
        
        # Tự động sao chép key vào clipboard
        root.clipboard_clear()
        root.clipboard_append(key)
        
        # Tự động điền Key vào ô nhập và bỏ ẩn ký tự để sẵn sàng cho bước Decrypt
        password_entry.delete(0, tk.END)
        password_entry.insert(0, key)
        password_entry.config(show="")
        
        messagebox.showinfo("Mã hóa thành công", "Đã mã hóa file thành công!\nChuỗi Key đã được tự động sao chép vào clipboard và điền vào ô nhập.")
    except Exception as e:
        messagebox.showerror("Lỗi mã hóa", str(e))
        result_label.config(text=f"Lỗi: {e}", fg="red")

def decrypt():
    file = filedialog.askopenfilename(title="Chọn file cần giải mã (.enc)")
    if not file:
        return
    pw = password_entry.get().strip()
    if not pw:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập hoặc dán chuỗi Key Base64 vào ô trên trước khi Decrypt!")
        return
    try:
        out = aes_utils.decrypt_file_aes(file, pw)
        result_label.config(text=f"Output: {out}", fg="green")
        messagebox.showinfo("Giải mã thành công", f"Giải mã hoàn tất!\nFile xuất ra: {out}")
    except Exception as e:
        messagebox.showerror("Lỗi giải mã", f"Giải mã thất bại: {e}\n\nNguyên nhân:\n1. Phải chọn file có đuôi '.enc'.\n2. Key Base64 phải đúng với lượt mã hóa của file đó.")
        result_label.config(text=f"Lỗi giải mã: {e}", fg="red")

root = tk.Tk()
root.title("SecureCrypto GUI")
root.geometry("480x200")

# Ô nhập mật khẩu / Key (mặc định ẩn ký tự khi nhập pass, tự hiện khi sinh Key)
password_entry = tk.Entry(root, show="*", width=42)
password_entry.pack(pady=8)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Encrypt", width=12, command=encrypt).pack(side=tk.LEFT, padx=8)
tk.Button(btn_frame, text="Decrypt", width=12, command=decrypt).pack(side=tk.LEFT, padx=8)

result_label = tk.Label(root, text="", wraplength=450, font=("Arial", 9))
result_label.pack(pady=10)

if __name__ == "__main__":
    root.mainloop()
