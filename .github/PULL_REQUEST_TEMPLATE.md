<!--
PRテンプレート / Mẫu Pull Request
JA: 5人チームなので「他の人に何が影響するか」を必ず書く。レビューは「動くか」でなく
    「規約(CONVENTIONS.md)と揃っているか」で見る。
VI: Nhóm 5 người nên BẮT BUỘC ghi "ảnh hưởng gì tới người khác". Review xét theo
    "có khớp CONVENTIONS.md không", KHÔNG chỉ "có chạy không".
-->

## 何をしたか / Đã làm gì
<!-- JA: 変更の概要を1〜3行で / VI: Tóm tắt thay đổi trong 1-3 dòng -->

## なぜ / Tại sao
<!-- JA: 背景・目的 / VI: Bối cảnh, mục đích -->

## 他メンバーへの影響 / Ảnh hưởng tới thành viên khác
<!--
JA: 共有物を触ったら必ず記載（触っていなければ「なし」）。例:
    - shared/ や apps/common/ を変更した
    - DBマイグレーションを追加した（migrate が必要）
    - 共通の型・APIの形を変えた
VI: Nếu chạm phần dùng chung thì phải ghi (không thì ghi "không có"). Ví dụ:
    - Sửa shared/ hoặc apps/common/
    - Thêm migration DB (cần chạy migrate)
    - Đổi kiểu chung / hình dạng API
-->

## 確認方法 / Cách kiểm tra
<!-- JA: 動作確認の手順 / VI: Các bước đã kiểm tra -->

## チェックリスト / Danh sách kiểm
- [ ] JA: CONVENTIONS.md に沿っている / VI: Tuân theo CONVENTIONS.md
- [ ] JA: HTTP通信は client.ts 経由 / VI: Giao tiếp HTTP qua client.ts
- [ ] JA: 業務ロジックは services.py / VI: Logic nghiệp vụ nằm ở services.py
- [ ] JA: CI（ruff / typecheck / build）が緑 / VI: CI xanh
- [ ] JA: マイグレーション漏れなし / VI: Không thiếu migration
