# Team App — モノレポ土台 / Nền tảng monorepo

JA: Django 5 + DRF（バックエンド）と React 18 + TypeScript + Vite（フロント・全画面SPA）の
モノレポの**土台**です。共通基盤（設定・認証・共通モデル・AI抽象化・フロントの通信/状態管理）と
**実装規約**を用意し、各機能は各担当が [`CONVENTIONS.md`](./CONVENTIONS.md) の**パターン（§9）**に沿って追加します。
VI: **Nền tảng** monorepo gồm Django 5 + DRF (backend) và React 18 + TypeScript + Vite (frontend, SPA toàn trang).
Cung cấp hạ tầng chung (cấu hình, xác thực, model chung, trừu tượng AI, giao tiếp/quản lý state frontend) và
**quy ước hiện thực**; mỗi tính năng do người phụ trách thêm theo **pattern (§9)** trong [`CONVENTIONS.md`](./CONVENTIONS.md).

> **開発規約は必ず [`CONVENTIONS.md`](./CONVENTIONS.md) を読むこと。AI に依頼する時も一緒に読ませる。**
> コード上に「見本機能」は置かず、実装パターンは同文書 §9 に集約しています。
> **Luôn đọc [`CONVENTIONS.md`](./CONVENTIONS.md). Khi nhờ AI cũng cho đọc kèm.**
> Không đặt "tính năng mẫu" trong code; pattern hiện thực gom ở §9 của tài liệu đó.

---

## 技術構成 / Stack

- Backend: **Django 5 + Django REST Framework**、認証は**セッション認証**（JWTは使わない）
- Frontend: **React 18 + TypeScript + Vite**（全画面SPA）、サーバ状態は **TanStack Query**
- DB: **SQLite**（ローカル）。`config/settings/production.py` で **PostgreSQL に切替可能**
- AI: **プロバイダ抽象化層**。既定は **fake 実装（APIキー不要）**。`AI_PROVIDER=gemini` で Gemini に切替（スケルトン）

---

## ディレクトリ構成 / Cấu trúc

```
.
├── CONVENTIONS.md          # 開発規約（最重要）/ Quy ước (quan trọng nhất)
├── .env.example            # 環境変数の雛形 / Mẫu biến môi trường
├── .github/                # CI・PRテンプレート
├── backend/
│   ├── config/             # 設定(base/local/production)・urls・wsgi/asgi
│   ├── apps/
│   │   ├── common/         # 基底モデル(UUID)・共通例外・IsOwner権限・seedコマンド
│   │   ├── accounts/       # カスタムUser・セッション認証API（共通基盤）
│   │   └── ai/             # LLM抽象化: base(Protocol)/fake/gemini/client
│   ├── requirements/       # base.txt / local.txt / gemini.txt
│   └── manage.py
└── frontend/
    └── src/
        ├── app/            # Provider・router・RequireAuth
        ├── pages/          # 組み立てのみ（HomePage=ログイン後の土台）
        ├── features/       # auth（共通基盤）。各機能はここに追加
        └── shared/         # api(client,queryKeys)・ui・types
```

---

## セットアップ / Cài đặt（clone → 起動）

前提 / Yêu cầu: **Python 3.13**, **Node 20+**

### 1. リポジトリ直下 / Ở gốc repo
```bash
cp .env.example .env      # 中身は空でOK（fake AIで動く）/ để trống cũng được (chạy fake AI)
```

### 2. バックエンド / Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements/local.txt
python manage.py migrate
python manage.py seed        # デモユーザーを投入 / nạp user demo
python manage.py runserver   # http://localhost:8000
```
> JA: リポジトリには既存の `myvenv/` があります。それを使う場合は
> `source myvenv/bin/activate` でも構いません（新規は上記 `.venv` を推奨）。
> VI: Repo có sẵn `myvenv/`. Nếu dùng nó thì `source myvenv/bin/activate` cũng được (khuyến nghị tạo mới `.venv`).

### 3. フロントエンド / Frontend（別ターミナル / terminal khác）
```bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

### 4. ログイン / Đăng nhập
ブラウザで **http://localhost:5173** を開く → `demo` / `demo12345` でログイン →
ホーム画面（ユーザー名＋ログアウト）が表示されます。ここから各自が機能を追加します。
Mở **http://localhost:5173** → đăng nhập `demo` / `demo12345` → thấy trang chủ (tên user + đăng xuất).
Từ đây mỗi người thêm tính năng của mình.

> `/api` は Vite が `:8000` にプロキシします（同一オリジン化でCookie/CSRFが素直に動く）。
> Vite proxy `/api` sang `:8000` (cùng origin để Cookie/CSRF chạy trơn tru).

---

## AI プロバイダ / Nhà cung cấp AI

JA: 既定は `AI_PROVIDER=fake` で、**APIキー無しで全員が開発可能**。Gemini を使うときだけ
`.env` に `AI_PROVIDER=gemini` と `GEMINI_API_KEY=...` を設定します（`gemini.py` は要実装）。
キー未設定で `gemini` を選んでも、安全のため自動で fake に退避します。
`google-generativeai`（Gemini公式SDK）は `requirements/local.txt` には含まれていません。
Windows ARM64など一部の環境で `grpcio`/`cryptography` のビルドに失敗するためです。
Gemini を実際に呼んで動作確認したい場合のみ `pip install -r requirements/gemini.txt` を実行してください。
VI: Mặc định `AI_PROVIDER=fake`, **không cần API key mọi người vẫn dev được**. Chỉ khi dùng Gemini
mới đặt `AI_PROVIDER=gemini` và `GEMINI_API_KEY=...` trong `.env` (`gemini.py` cần được cài).
Nếu chọn `gemini` mà thiếu key, hệ thống tự lùi về fake cho an toàn.
`google-generativeai` (SDK chính thức của Gemini) không nằm trong `requirements/local.txt`,
vì một số môi trường (vd. Windows ARM64) sẽ build lỗi `grpcio`/`cryptography`.
Chỉ khi thực sự cần gọi Gemini để kiểm tra, hãy chạy `pip install -r requirements/gemini.txt`.

---

## まだ作っていないもの・なぜ / Chưa làm & vì sao

| 未実装 / Chưa có | 理由 / Lý do |
|---|---|
| すべての機能アプリ（`chat` `practice` 等）とフロント feature | JA: **意図的に未実装**。コード上の見本を置かず、各担当が [`CONVENTIONS.md`](./CONVENTIONS.md) §9 のパターンに沿って §4/§5 の手順で追加する。DB設計が固まってから着手。 VI: **Cố ý chưa làm.** Không đặt mẫu trong code; mỗi người thêm theo pattern §9 và các bước §4/§5 của [`CONVENTIONS.md`](./CONVENTIONS.md). Bắt đầu sau khi chốt thiết kế DB. |
| フロントの `entities/` 層 | JA: 規模が小さいため。ドメイン型は当面 `shared/types` に置く。必要になったら導入。 VI: Quy mô nhỏ. Kiểu domain tạm để ở `shared/types`, khi cần mới thêm. |
| `gemini.py` の本実装 | JA: スケルトンのみ。fake で開発できるため後回し可。AI担当が実装。 VI: Chỉ có khung. Dev bằng fake nên để sau; người phụ trách AI hiện thực. |
| 本番デプロイ設定 | JA: `production.py` はPostgreSQL切替の受け皿まで。デプロイ手順は別途。 VI: `production.py` mới tới mức chuyển PostgreSQL. Quy trình deploy để riêng. |

---

## Git 運用 / Quy trình Git

- `main` は保護。直接 push しない。作業ブランチは `develop` から切り、**`develop` へ PR**。
- ブランチ名: `feat/<機能>` `fix/<内容>` `chore/<内容>`。
- PR テンプレに従い**他メンバーへの影響**を記載。**CI が緑になってからマージ**。
- 詳細は [`CONVENTIONS.md`](./CONVENTIONS.md) §7。

---

## 動作確認 / Kiểm tra nhanh

```bash
# backend
cd backend && ruff check . && ruff format --check . \
  && python manage.py makemigrations --check --dry-run
# frontend
cd frontend && npm run typecheck && npm run build
```
