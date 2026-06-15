# Hướng Dẫn Sử Dụng — Kết Nối Amazon Ads với AI

> Dành cho mọi người, **không cần biết lập trình**. Làm theo đúng thứ tự là chạy được.
> Cả quá trình mất khoảng **15 phút**, chỉ làm **1 lần duy nhất**.

---

## 0. Bạn sẽ có gì sau khi làm xong?

Trợ lý AI (Claude / Codex...) nói chuyện trực tiếp với tài khoản Amazon Ads của bạn.
Ví dụ bạn gõ:

> *"Liệt kê các chiến dịch đang chạy của tôi"*
> *"Chiến dịch nào có ACOS trên 40% trong 30 ngày qua?"*
> *"Tạm dừng các chiến dịch không có đơn nào trong 14 ngày"*

→ AI tự làm, không cần vào dashboard Amazon thủ công.

---

## 1. Chuẩn bị (5 phút)

### a) Cài Python (phần mềm chạy nền)

- **Máy Mac:** Mở ứng dụng **Terminal** (bấm `Cmd + dấu cách`, gõ "Terminal", Enter).
  Gõ dòng này rồi Enter:
  ```
  python3 --version
  ```
  Nếu hiện ra số (vd `Python 3.12`) → đã có, bỏ qua. Nếu báo lỗi → tải tại
  https://www.python.org/downloads/ , cài như app bình thường.

- **Máy Windows:** Vào https://www.python.org/downloads/ → tải bản mới nhất →
  **khi cài nhớ tích ô "Add Python to PATH"** (rất quan trọng) → Next đến hết.

### b) Xin 2 mã từ trưởng nhóm

Nhắn trưởng nhóm (team lead) xin:
- **Client ID** (chuỗi bắt đầu bằng `amzn1.application-oa2-client...`)
- **Client Secret** (chuỗi bí mật)

> 2 mã này dùng chung cho cả team. **Giữ kín**, đừng gửi lên nhóm chat công khai.

### c) Tải bộ cài

Trưởng nhóm sẽ gửi bạn link tải (GitHub) hoặc 1 file nén.
- Nếu là **file nén (.zip)**: giải nén ra một thư mục.
- Nếu là **link GitHub**: bấm nút xanh **Code → Download ZIP**, rồi giải nén.

Ghi nhớ thư mục vừa giải nén (ví dụ để ở Desktop cho dễ tìm).

---

## 2. Chạy cài đặt (5 phút)

### Mở cửa sổ dòng lệnh tại đúng thư mục

- **Mac:** Mở **Terminal**, gõ `cd ` (có dấu cách), rồi **kéo thả thư mục vừa giải nén**
  vào cửa sổ Terminal → Enter.
- **Windows:** Mở thư mục vừa giải nén trong File Explorer → bấm vào thanh địa chỉ ở
  trên → gõ `powershell` → Enter.

### Gõ lệnh cài đặt

Gõ đúng dòng này rồi Enter:

```
python3 scripts/setup.py
```

> Windows: nếu báo lỗi "không tìm thấy python3", thử lại với `python scripts/setup.py`.

### Làm theo hướng dẫn trên màn hình

1. Nó hỏi **Client ID** → dán mã trưởng nhóm gửi → Enter.
2. Hỏi **Client Secret** → dán mã → Enter. *(Lưu ý: khi dán mật khẩu màn hình KHÔNG
   hiện ký tự — đó là bình thường, cứ dán rồi Enter.)*
3. Hỏi **REGION** → gõ `NA` (Bắc Mỹ — US/CA/MX/BR). Nếu bán ở Châu Âu gõ `EU`,
   Châu Á gõ `FE`.
4. **Trình duyệt tự mở** → đăng nhập tài khoản Amazon của bạn → bấm **Allow / Cho phép**.
5. Quay lại cửa sổ dòng lệnh → đợi nó in ra danh sách tài khoản quảng cáo của bạn.

✅ Khi thấy dòng **"Setup complete"** là xong phần cài đặt.

---

## 3. Kết nối vào AI (3 phút)

Cuối bước cài đặt, màn hình in ra phần cấu hình cho từng app. Làm theo app bạn dùng:

### Nếu dùng Claude Desktop (app trên máy)

1. Mở app **Claude**.
2. Vào **Settings (Cài đặt) → Developer → Edit Config** (hoặc mở file cấu hình mà
   màn hình đã chỉ đường dẫn).
3. Dán đoạn cấu hình màn hình đã in ra (phần "CLAUDE DESKTOP").
4. **Thoát hẳn Claude** (Mac: `Cmd+Q`) rồi mở lại.

### Nếu dùng Claude Code (dòng lệnh)

Chỉ cần copy đúng 1 dòng lệnh màn hình in ra (phần "CLAUDE CODE"), dán vào Terminal, Enter.

### Nếu dùng Codex / Cursor

Mở file `docs/clients.md` trong bộ cài, copy đoạn tương ứng với app của bạn.

---

## 4. Kiểm tra hoạt động

Trong khung chat của AI, gõ:

```
Liệt kê các tài khoản quảng cáo Amazon mà tôi có quyền truy cập
```

Nếu AI trả về danh sách tài khoản → **thành công! 🎉**

---

## ⚠️ Lưu ý quan trọng

- **2 tuần đầu chỉ nên hỏi xem báo cáo** (số liệu, hiệu suất). Đừng vội cho AI tạo/xóa/sửa
  chiến dịch cho tới khi bạn tin tưởng số liệu nó đưa ra.
- AI **có thể tạo và xóa chiến dịch thật** → luôn đọc kỹ trước khi xác nhận.
- Mã **Client Secret** và tài khoản Amazon của bạn là **riêng tư** — không chia sẻ.

---

## ❓ Gặp lỗi thì làm gì?

| Hiện tượng | Cách xử lý |
|---|---|
| AI báo "không kết nối được" | Khởi động lại máy, đợi 1 phút rồi thử lại. Vẫn lỗi → báo IT. |
| Cài đặt báo lỗi token / 401 | Chạy lại `python3 scripts/setup.py` để đăng nhập lại. |
| Trình duyệt không tự mở | Copy đường link màn hình in ra, dán vào trình duyệt thủ công. |
| Không biết gõ lệnh ở đâu | Xem lại Mục 2 "Mở cửa sổ dòng lệnh", hoặc nhờ đồng nghiệp/IT. |

Mọi thắc mắc khác: nhắn **trưởng nhóm** hoặc **bộ phận IT**.

---

*Bạn chỉ cần cài 1 lần. Sau đó mỗi lần bật máy, kết nối tự chạy nền — cứ mở AI lên là dùng.*
