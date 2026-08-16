# フォルダ構成ガイド（日本語版）

> このリポジトリの各フォルダが「何のためにあり」「中のファイルに何を書くべきか」を
> 端的にまとめたものです。詳しい実装ルール・コピー元パターンは必ず
> [`CONVENTIONS.md`](./CONVENTIONS.md) を読んでください。セットアップ手順は
> [`README.md`](./README.md) を参照してください。本書はその前段にある「地図」です。

---

## 全体像

```
.
├── CONVENTIONS.md   # 開発規約（最重要・実装パターン集）
├── README.md        # セットアップ手順
├── .env.example     # 環境変数のひな形
├── .github/         # CI・PRテンプレート
├── backend/         # Django + DRF（サーバー側）
└── frontend/        # React + TypeScript + Vite（画面側／SPA）
```

バックエンドとフロントエンドは **`/api/...` という URL と JSON の形だけ** でやり取りします。
それぞれ独立したフォルダで、直接コードを import し合うことはありません。

---

## 1. リポジトリ直下

| ファイル / フォルダ | 役割 | 何を書く・編集するか |
|---|---|---|
| `CONVENTIONS.md` | 開発規約。§9 に全レイヤーの実装パターン（コピー元）がある | 規約自体を変える時のみ編集。通常は「読む」専用 |
| `README.md` | セットアップ手順・技術構成の説明 | セットアップ方法が変わったら更新 |
| `.env.example` | 環境変数のひな形 | 新しい環境変数を追加したらキーだけ追記（値は空） |
| `.github/workflows/ci.yml` | CI定義（backend: ruff・migration漏れチェック / frontend: 型チェック・build） | 通常は触らない。CIの検査項目を増やす時だけ編集 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR作成時に自動で読み込まれるテンプレート | 通常は触らない |

---

## 2. `backend/`（Django + DRF）

### 直下ファイル

| ファイル | 役割 | 何を書くか |
|---|---|---|
| `manage.py` | Django コマンドの入口 | 基本編集しない |
| `requirements/base.txt` | 全環境共通の依存パッケージ | 新しい pip パッケージが要るなら追記 |
| `requirements/local.txt` | 開発専用ツール（lint等） | 開発専用パッケージが要るなら追記 |
| `requirements/gemini.txt` | Gemini SDK（`google-generativeai`）用のオプション依存 | Windows ARM64等でビルド失敗するため分離。Gemini実動作確認時のみ `pip install -r requirements/gemini.txt` |

### `backend/config/` — プロジェクト全体の設定（「地図」役）

| ファイル | 役割 | 何を書くか |
|---|---|---|
| `settings/base.py` | 全環境共通の設定 | 新しい `INSTALLED_APPS` や DRF 設定など、環境に依存しないものを追記 |
| `settings/local.py` | ローカル専用の上書き（SQLite・DEBUG・CORS） | 通常触らない |
| `settings/production.py` | 本番用（PostgreSQL切替の受け皿・未使用） | デプロイ担当が拡張 |
| `urls.py` | プロジェクト全体のURL入口 | **新しいアプリを作ったら `include()` を1行追加** |
| `wsgi.py` / `asgi.py` | サーバー起動口 | 通常編集しない |

### `backend/apps/` — 機能ごとの Django アプリを置く場所

各アプリは標準の5点セット `models.py` / `serializers.py` / `services.py` / `views.py` / `urls.py`（＋`admin.py`）
で構成します。**`views/` や `models/` のようなレイヤーフォルダには分けません。**

依存の向きは **`views → services → models`**（逆流禁止）。

| ファイル | 書くこと | 書かないこと |
|---|---|---|
| `models.py` | テーブル定義・リレーション | 業務ロジック |
| `serializers.py` | JSONの形の定義・入力検証 | 保存処理・業務判断 |
| `services.py` | **業務ロジック（HTTPを知らない純粋な関数）** | `request` や HTTP を触ること |
| `views.py` | 認可・入力検証・**services呼び出し**・シリアライズ | 業務ロジックそのもの |
| `urls.py` | このアプリ内のルーティング登録 | それ以外 |
| `admin.py` | Django管理画面への登録 | — |

#### `apps/common/`（全アプリ共通の土台。機能固有ロジックは絶対に書かない）

| ファイル | 役割 |
|---|---|
| `models.py` | `BaseModel`（UUID主キー＋作成/更新日時）。新規モデルはこれを継承するだけで、直接編集は稀 |
| `exceptions.py` | `ValidationError` 等のドメイン例外とDRF例外ハンドラ。新しい種類のエラーが必要な時だけ追記 |
| `permissions.py` | `IsOwner` など共通権限クラス。新しい共通権限が要る時だけ追記 |
| `management/commands/seed.py` | デモデータ投入コマンド。**自分の機能のダミーデータ生成をここに追記してよい** |

#### `apps/accounts/`（ユーザー認証。この構成が全機能アプリの「手本」）

| ファイル | 内容 |
|---|---|
| `models.py` | カスタム `User`（フィールドは意図的に空）。基本触らない |
| `serializers.py` | ログイン入出力の型・検証のみ |
| `services.py` | 資格情報の検証（純粋な判断ロジック） |
| `views.py` | `/api/auth/{csrf,login,logout,me}/` のAPI。認可・セッション制御 |
| `urls.py` | 認証エンドポイントの定義 |

#### `apps/ai/`（LLMプロバイダの抽象化層。DBモデルは持たない）

| ファイル | 役割 |
|---|---|
| `base.py` | 全プロバイダが満たすべき契約（`Protocol`）。むやみに変更しない |
| `fake.py` | APIキー不要のダミー実装。既定はこれが使われる |
| `gemini.py` | 本実装（未実装スケルトン）。**AI担当が中身を実装する** |
| `client.py` | 呼び出しの唯一の窓口。`get_llm()` 経由で使う（fake/geminiの切替はここでのみ発生） |

#### 新しい機能アプリを作るとき（例: `apps/items/`）

[`CONVENTIONS.md` §4](./CONVENTIONS.md) の手順に従い、`apps/accounts/` と同じ5点セットで作成します。
実装の雛形は必ず [`CONVENTIONS.md` §9](./CONVENTIONS.md) からコピーしてください（コード上に見本機能は置かない方針）。

---

## 3. `frontend/`（React + TypeScript + Vite）

Feature-Sliced 寄りの構成で、依存は **上から下への一方向**です。

```
app/       … Provider・ルーター・レイアウト（最上位の組み立て）
  ↓
pages/     … ルート単位。部品を並べる「組み立て」だけ
  ↓
features/  … 機能ごと（api フック + components）。ここに機能の中身
  ↓
shared/    … api クライアント・共通UI・型（全 feature の土台）
```

### `frontend/src/app/` — アプリの土台

| ファイル | 役割 | 何を書くか |
|---|---|---|
| `App.tsx` | アプリのルート。Providerでルーターを包むだけ | 基本触らない |
| `providers.tsx` | 全体を包む Provider（TanStack Query 等）を集約 | 新しいグローバル Provider が必要な時だけ追記 |
| `router.tsx` | URL と page の対応表 | **新しい画面を作ったらここに1行追加** |
| `RequireAuth.tsx` | 認証ガード（未ログインならログイン画面へ） | 通常触らない |

### `frontend/src/pages/` — 画面の「組み立てのみ」

- 1画面 = 1ファイル（例: `HomePage.tsx`, `LoginPage.tsx`）。
- `features/` の components を並べるだけで、**業務ロジック・通信を書いてはいけない**。
- 新しい画面を作ったら `app/router.tsx` にルートを1行追加する。

### `frontend/src/features/<機能名>/` — 機能ごとの実装（中身はここに書く）

| フォルダ | 役割 | 何を書くか |
|---|---|---|
| `api/hooks.ts` | サーバ状態を扱う TanStack Query フック | `useQuery`/`useMutation`。**通信は必ず `shared/api/client.ts` の `api` 経由**。`fetch` を直接呼ばない |
| `api/mockData.ts` | バックエンドAPI未実装時の仮データ・仮ロジック | 実装後は `api/hooks.ts` からの実APIコールに置き換える |
| `components/` | 表示コンポーネント | UIとフックの結線。通信ロジックは持ち込まない |

**厳守**: `features/` 同士は直接 import しない。共有したくなったら `shared/` へ上げる。

### `frontend/src/shared/` — 全 feature 共通の土台

| ファイル/フォルダ | 役割 | 何を書くか |
|---|---|---|
| `api/client.ts` | **全HTTP通信の唯一の入口**（Cookie送信・CSRF付与・401リダイレクト・エラー整形） | 認証やエラー処理の方針を変える時のみ編集。個々の機能はここを呼ぶだけ |
| `api/queryKeys.ts` | TanStack Query のクエリキーを一元管理 | **新機能を作るたびに、ここにキーを1グループ追加** |
| `types/index.ts` | 複数 feature で共有する型 | バックエンドのシリアライザ出力と形を合わせて追記。feature固有の型は各feature内に置く |
| `ui/index.tsx` | 全feature共通の最小限UI部品（Button/Input/Notice等） | 「どの機能にも依存しない」汎用部品のみ。業務ロジックを持ち込まない |
| `lib/` | 共通ロジック・ユーティリティ置き場（現在は空） | 複数featureで使う汎用関数が必要になったら追加 |

### `frontend/` 直下

| ファイル | 役割 | 何を書くか |
|---|---|---|
| `vite.config.ts` | devサーバ設定・`/api`のプロキシ設定 | 通常触らない |
| `tsconfig.json` | TypeScript設定・パスエイリアス(`@/`) | 通常触らない |
| `package.json` | 依存パッケージ・npmスクリプト | 新しいパッケージを追加したら更新される |

---

## 補足説明（経験レベル別）

### 🅰 React / Next.js 経験者向け（Djangoが初めての人向け）

- **`apps/<name>/` は Next.js の「機能ごとのフォルダ」に近いですが、ファイルベースルーティングではありません。**
  Next.js は `app/items/page.tsx` を作れば自動的に `/items` になりますが、Django は
  `apps/items/urls.py` に自分でパスを書き、さらに `config/urls.py` に `include()` を追加しないと
  URLが有効になりません。「フォルダを作れば勝手にルートになる」感覚は通用しません。
- **`views.py` は Next.js の Route Handler（`app/api/.../route.ts`）に近い存在ですが、
  この規約では中身をほぼ書きません。** ロジックは必ず `services.py` に書き、`views.py` は
  「認可・入力検証・呼び出し・シリアライズ」の薄いコントローラーに徹します。
- **`serializers.py` は Zod や Yup のスキーマ定義に近い**（型定義＋バリデーション）ですが、
  DBモデル（`models.py`）とJSONの変換も兼ねる点がフロントのバリデーションライブラリと異なります。
- **`models.py`（Django ORM）は Prisma の `schema.prisma` に近い概念**です。
  `python manage.py makemigrations` が `prisma migrate dev` に相当します。
- **`config/settings/`（base/local/production）は `next.config.js` ＋ `.env.*` をまとめて
  Python化したようなもの**です。ただし1ファイルではなく環境ごとに分割されている点に注意してください
  （`local.py` が `base.py` を上書きする形）。
- フロント側 (`app/`・`pages/`・`features/`・`shared/`) は見慣れた構成のはずですが、
  **Next.js の `app/` ディレクトリとは役割が違います**。ここでの `app/` は「Provider や
  ルーター定義を置く場所」であり、ルーティングそのものは `react-router-dom` を使って
  `router.tsx` に明示的に書きます（Next.jsのようにフォルダ構造＝ルートではありません）。

### 🅱 Django 経験者向け（React/Next.jsが初めての人向け）

- **`frontend/src/features/` は Django の `apps/` と発想は同じ「機能単位の分割」です。**
  ただしフロント側は1機能＝1フォルダの中に `api/`（データ取得ロジック）と `components/`
  （見た目）の2つしかなく、Djangoほど多くのファイル種別に分かれません。
- **`pages/` は Django の `templates/` に近い立ち位置ですが、規約がより厳格です。**
  `pages/` は本当に「部品を並べるだけ」で、通信もロジックも一切書いてはいけません
  （中身は必ず `features/` に書く）。
- **`shared/api/client.ts` は、Djangoでいう「共通のリクエストラッパー／ミドルウェア」に相当**します。
  Cookie送信・CSRFトークン付与・エラー処理をここに一本化することで、`apps/common/exceptions.py`
  が担っている「例外を1箇所に集約する」設計思想と同じことをフロント側でも行っています。
- **TanStack Query（`api/hooks.ts` で使用）は、サーバから取得したデータをブラウザ側で
  キャッシュ・管理するライブラリ**です。Djangoのセッションのようにサーバ側で状態を持つのとは別に、
  フロント側でも「このデータはいつ再取得するか」を管理する必要がある、と考えるとイメージしやすいです。
  `useQuery` = データ取得＋キャッシュ、`useMutation` = 更新系（POST/PUT/DELETE）、と対応します。
- **CSRF対策は Django のテンプレート機能（`{% csrf_token %}`）が使えない代わりに、
  SPA側（`shared/api/client.ts`）が `csrftoken` Cookie を自分で読み取ってヘッダーに
  手動で付与しています。** これは Django 側の CSRF ミドルウェアの仕組みは変わらず、
  「トークンの受け渡し方法」だけがSPA向けに変わっている、と理解してください。

### 🆕 両方とも未経験の人向け

- **`backend/` はサーバー側（裏方）です。** データベースへの保存・ログイン確認など、
  ブラウザの画面には直接映らない処理を担当します。
- **`frontend/` はブラウザに実際に表示される画面そのものです。** ユーザーがクリックしたり
  文字を入力したりするボタンやフォームは、すべてここにあります。
- **両者は「API」という共通の約束事だけでつながっています。** `backend/` が
  `/api/items/` のようなURLを用意し、`frontend/` の `shared/api/client.ts` がそのURLに
  リクエストを送って結果（JSON）を受け取る、という関係です。お互いのコードを直接
  読み込んだりはしません。
- **1つの機能を作る時は「バックエンドとフロントエンドはペアで作る」と考えると分かりやすいです。**
  例えば「アイテム管理」機能なら、`backend/apps/items/` と `frontend/src/features/items/` の
  **両方**を作ることになります。
- 何から手をつければよいか迷ったら、まず [`CONVENTIONS.md`](./CONVENTIONS.md) の
  **§9（実装パターン）** をそのままコピーして、名前だけ自分の機能名に置き換えて動かしてみるのが
  一番の近道です。実際に動くコードを触りながら、この文書の各行が指す場所を確認してみてください。
