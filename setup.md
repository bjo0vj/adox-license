# AdoExport License Server — Hướng dẫn Setup

## Đăng nhập Admin

- **Username:** `bjo0vj`
- **Password:** `Phat@0833`

---

## Bước 1: Tạo GitHub repo (chứa code server)

1. Vào https://github.com/new
2. **Repository name:** `adox-license` (hoặc tên gì cũng được, private)
3. Chọn **Private** → bấm **Create repository**
4. GitHub hiện trang hướng dẫn, mở terminal chạy:

```bash
cd "c:\Users\phatt\Downloads\Adoexport\server"
git init
git add .
git commit -m "license server"
git branch -M main
git remote add origin https://github.com/bjo0vj/adox-license.git
git push -u origin main
```

> Đã cập nhật `YOUR_USERNAME` thành `bjo0vj`.
> Nếu chưa cài Git: https://git-scm.com/download/win → tải về cài, mặc định hết.

---

## Bước 2: Deploy lên Render

1. Vào https://render.com → **Sign up** (đăng ký bằng GitHub cho nhanh)
2. Sau khi đăng nhập, bấm **New +** (góc trên phải) → **Web Service**
3. Chọn **Build and deploy from a Git repository** → **Next**
4. Tìm repo `adox-license` vừa push → bấm **Connect**
5. Điền thông tin:

| Mục | Giá trị |
|-----|---------|
| **Name** | `adox` (càng ngắn càng tốt, URL sẽ là `https://adox.onrender.com`) |
| **Region** | Singapore (gần VN nhất) hoặc Oregon |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |
| **Instance Type** | **Free** |

6. Kéo xuống mục **Environment Variables**, bấm **Add Environment Variable** 3 lần:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | bấm nút **Generate** |
| `ADMIN_USER` | `bjo0vj` |
| `ADMIN_PASS` | `Phat@0833` |

7. Bấm **Create Web Service**
8. Đợi build (1-3 phút), khi thấy **==> Your service is live 🎉** là xong

### Kiểm tra

Mở trình duyệt:
- `https://adox.onrender.com/` → thấy `{"status":"ok"}` ✓
- `https://adox.onrender.com/ping` → thấy `pong` ✓
- `https://adox.onrender.com/admin` → thấy trang login ✓

---

## Bước 3: Setup UptimeRobot (giữ server chạy 24/7)

Render free tự tắt server sau 15 phút không có request.
UptimeRobot ping mỗi 5 phút → server không bao giờ ngủ.

1. Vào https://uptimerobot.com → **Register for FREE**
2. Đăng ký xong, vào Dashboard → bấm **+ Add New Monitor**
3. Điền:

| Mục | Giá trị |
|-----|---------|
| **Monitor Type** | `HTTP(s)` |
| **Friendly Name** | `AdoExport License` |
| **URL (or IP)** | `https://adox.onrender.com/ping` |
| **Monitoring Interval** | `5 minutes` |

4. Bấm **Create Monitor**

Xong. Server chạy liên tục, UptimeRobot tự ping mỗi 5 phút.

---

## Bước 4: Patch exe

URL `https://adox.onrender.com` = 25 chars ≤ 32 ✓

Mở terminal tại thư mục Adoexport:
```bash
cd "c:\Users\phatt\Downloads\Adoexport"
python patch_exe2.py https://adox.onrender.com
```

Output:
```
New URL: https://adox.onrender.com/aaaaaa/ (32 bytes)
Found at offset 0x0347CFEC
Patched: ...adoexport.exe
```

File `adoexport.exe` đã được patch, sẵn sàng dùng.

> **Nếu tên service khác `adox`:** thay URL tương ứng, miễn ≤ 32 chars.

---

## Bước 5: Sử dụng

1. Mở `https://adox.onrender.com/admin` → đăng nhập `bjo0vj` / `Phat@0833`
2. Tạo key: chọn số lượng, thời hạn (days/months/years/lifetime), bấm **Generate**
3. Copy key (dạng `ADOX-XXXX-XXXX-XXXX`)
4. Gửi key cho user
5. User chạy `adoexport.exe` đã patch → nhập key → done

### Admin panel chức năng:
- **Generate:** tạo key hàng loạt (tối đa 100 cái/lần)
- **Off/On:** tắt/bật key
- **Unbind:** gỡ bind máy (cho user đổi máy)
- **Del:** xóa key
- **Note:** ghi chú (tên khách, gói,...)
- **Logs:** xem 50 log gần nhất (ai verify, lúc nào, IP nào)

---

## Lưu ý

### ⚠️ SQLite trên Render Free — DB sẽ reset khi redeploy
- Mỗi lần push code mới hoặc Render tự restart → `license.db` bị xóa
- Key đã tạo sẽ **mất hết**
- Fix: đừng push code liên tục, chỉ push khi thật sự cần update
- Nếu cần DB bền vững:
  - Render Starter ($7/tháng) có persistent disk
  - Hoặc đổi sang dùng PostgreSQL free của Render (cần sửa code)

### URL phải ≤ 32 ký tự
- `https://adox.onrender.com` = 25 chars ✓
- `https://adoexport-license.onrender.com` = 39 chars ✗ (quá dài!)
- Đặt tên service ngắn: `adox`, `lcs`, `ado`,...

### Đổi mật khẩu admin
- Vào Render Dashboard → chọn service → **Environment** → sửa `ADMIN_PASS` → **Save Changes**
- Service tự restart, password mới có hiệu lực ngay
