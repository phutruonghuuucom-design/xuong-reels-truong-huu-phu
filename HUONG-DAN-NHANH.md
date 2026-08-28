# 🎬 Hướng dẫn nhanh — App edit video Reels Hưng Huỳnh

Chào bạn! Làm theo 4 bước dưới là dùng được. Chỉ chạy trên **máy Mac**.

---

## Cần có trước
- Một máy **Mac** (MacBook / iMac).
- **Claude Code** đã cài (app để chạy skill này). Chưa có thì tải ở: https://claude.ai/download
- (Bước cài sẽ tự tải thêm ffmpeg — nếu máy hỏi cài **Homebrew**, vào https://brew.sh làm theo, rồi quay lại.)

---

## Bước 1 — Giải nén
Bấm đúp vào file **`edit-video-reels-coban.zip`** → ra thư mục **`edit-video-reels-coban`**.

## Bước 2 — Cài công cụ (làm 1 lần)
1. Mở app **Terminal** (bấm phím `Cmd + dấu cách`, gõ *Terminal*, Enter).
2. Trong Terminal, gõ chữ `bash` rồi **1 dấu cách**.
3. **Kéo file `cai-dat.sh`** từ thư mục vừa giải nén **thả vào cửa sổ Terminal** (nó tự điền đường dẫn).
4. Bấm **Enter**. Chờ nó cài xong (vài phút, có mạng).

> Xong sẽ thấy dòng: *"🎉 XONG..."*

## Bước 3 — Đưa skill vào đúng chỗ
1. Trong **Finder**, bấm menu **Đi (Go) → Đi tới thư mục…** (hoặc `Cmd + Shift + G`).
2. Gõ:  `~/.claude/skills`  → Enter. (Nếu chưa có thư mục `skills` thì tạo mới tên `skills`.)
3. **Kéo cả thư mục `edit-video-reels-coban`** vào đây.

## Bước 4 — Dùng
1. Mở **Claude Code**.
2. Gõ:  **edit video reels**  rồi đưa (kéo) 1 video quay mặt nói vào.
3. Làm theo hướng dẫn trên màn hình → ra video Reels dọc có phụ đề, badge, màu đẹp.

---

## Muốn làm từ ĐIỆN THOẠI (máy Mac làm hộ)
1. Trên Mac: mở Terminal, gõ `bash ` rồi **kéo thả file `chay-server.sh`** vào → Enter.
2. Màn hình hiện 1 link kiểu `http://192.168.x.x:8000`.
3. Lấy **điện thoại cùng wifi** với Mac, mở link đó bằng Safari/Chrome.
4. Chọn video → bấm **Làm reel** → chờ → **Tải video** về.
   (Mac phải đang bật + chạy. Nếu máy hỏi *"cho phép python nhận kết nối"* → bấm **Allow**.)

---

## Kẹt chỗ nào?
- **"command not found"** khi cài → gõ lại: `python3 -m pip install --user Pillow openai-whisper`
- **Render chậm** → bình thường, video 4K nặng. Cứ chờ, hoặc dùng video ngắn.
- **Điện thoại không mở được link** → kiểm tra có đúng wifi của Mac không; Mac còn chạy server không.

Chúc bạn làm video vui! 🎥
