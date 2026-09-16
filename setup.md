# AdoExport License Server — Hướng dẫn Setup (Railway)

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

## Bước 2: Deploy lên Railway

1. Vào https://railway.app → **Login** bằng GitHub
2. Bấm **New Project** → **Deploy from GitHub repo**
3. Chọn repo `adox-license` → bấm **Deploy Now**
4. Railway tự detect Python, cài `requirements.txt`, dùng `railway.toml` để start

### Thêm Environment Variables

Vào project → chọn service → tab **Variables** → bấm **+ New Variable**, thêm 3 biến:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | gõ 1 chuỗi ngẫu nhiên dài (vd: `abc123xyz456...`) |
| `ADMIN_USER` | `bjo0vj` |
| `ADMIN_PASS` | `Phat@0833` |

> Railway tự redeploy sau khi thêm biến.

### Tạo domain public

1. Vào service → tab **Settings** → mục **Networking** (hoặc **Public Networking**)
2. Bấm **Generate Domain**
3. Được URL dạng: `https://adox-license-production-xxxx.up.railway.app`

> ⚠️ URL Railway thường dài. Nếu quá 32 chars → vào **Settings** → **Custom Domain** đặt domain ngắn, hoặc dùng **Change Domain** để chỉnh prefix ngắn lại.

### Kiểm tra

Mở trình duyệt:
- `https://<YOUR-DOMAIN>.up.railway.app/` → thấy `{"status":"ok"}` ✓
- `https://<YOUR-DOMAIN>.up.railway.app/ping` → thấy `pong` ✓
- `https://<YOUR-DOMAIN>.up.railway.app/admin` → thấy trang login ✓

---

## Bước 3: Thêm Volume (giữ DB không mất)

Railway hỗ trợ Volume — gắn ổ đĩa bền vững, DB không bị xóa khi redeploy.

1. Trong project, bấm **+ New** → **Volume**
2. Điền:
   - **Name:** `data`
   - **Mount Path:** `/app/data`
3. Bấm **Add**
4. Vào tab **Variables**, thêm:

| Key | Value |
|-----|-------|
| `DB_PATH` | `/app/data/license.db` |

> Service tự redeploy. Từ giờ `license.db` nằm trong volume, **không mất** khi redeploy.

---

## Bước 4: Patch exe

Lấy URL Railway của bạn (vd: `https://adox.up.railway.app`).

> URL phải ≤ 32 ký tự. Nếu dài quá → dùng custom domain ngắn.

Mở terminal tại thư mục Adoexport:
```bash
cd "c:\Users\phatt\Downloads\Adoexport"
python patch_exe2.py https://adox.up.railway.app
```

Output:
```
New URL: https://adox.up.railway.app/aa/ (32 bytes)
Found at offset 0x0347CFEC
Patched: ...adoexport.exe
```

File `adoexport.exe` đã được patch, sẵn sàng dùng.

> **Thay URL đúng với domain Railway của bạn.**

---

## Bước 5: Sử dụng

1. Mở `https://<YOUR-DOMAIN>.up.railway.app/admin` → đăng nhập `bjo0vj` / `Phat@0833`
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

### ✅ Railway có Volume — DB bền vững
- Đã setup Volume ở Bước 3 → `license.db` **không mất** khi redeploy
- Nếu chưa gắn Volume → DB nằm trên ephemeral disk, mất khi redeploy

### URL phải ≤ 32 ký tự
- `https://adox.up.railway.app` = 28 chars ✓
- URL mặc định Railway thường dài → cần chỉnh prefix ngắn hoặc dùng custom domain
- Vào **Settings** → **Networking** → sửa domain prefix cho ngắn

### Đổi mật khẩu admin
- Vào Railway Dashboard → chọn service → **Variables** → sửa `ADMIN_PASS`
- Service tự redeploy, password mới có hiệu lực ngay

### Railway free tier
- $5 credit miễn phí mỗi tháng (đủ chạy 24/7 cho app nhẹ)
- Không cần UptimeRobot — Railway **không tự sleep** như Render
- Nếu hết credit → service tạm dừng, tháng sau reset
