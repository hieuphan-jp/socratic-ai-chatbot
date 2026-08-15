# CONVENTIONS.md — 開発規約 / Quy ước phát triển

> **この文書の使い方 / Cách dùng tài liệu này**
> JA: AI に作業を頼むたびに、この文書を一緒に読ませてください。5人＋各AIの出力を揃えるための共通ルールです。
> **この文書が唯一の見本です**（コード上の「見本機能」は置きません）。§9 のパターンをコピー元にしてください。
> VI: Mỗi lần nhờ AI làm việc, hãy cho AI đọc kèm tài liệu này. Đây là luật chung để đồng nhất output của 5 người + các AI.
> **Tài liệu này là mẫu duy nhất** (không đặt "tính năng mẫu" trong code). Dùng pattern ở §9 làm nguồn để sao chép.

> **採用の判断基準 / Tiêu chí chấp nhận code**
> JA: AI が書いたコードは「**動くか**」ではなく「**他の4人と揃っているか**」で採用を判断します。
> 動いていても本規約（特に §9 のパターン）と形が違うなら、揃える方向に直してからマージします。
> VI: Code do AI viết được chấp nhận dựa trên "**có khớp với 4 người còn lại không**", KHÔNG phải "**có chạy không**".
> Dù chạy được nhưng khác quy ước (nhất là pattern §9) thì phải sửa cho khớp rồi mới merge.

---

## 1. バックエンドのレイヤー責務 / Trách nhiệm các tầng backend

各 Django アプリは標準の形（`models.py` / `views.py` / `serializers.py` / `services.py` / `urls.py` / `admin.py`）。
**`views/` や `models/` のようなレイヤーフォルダには分けません**（Django のアプリ単位分割に従う）。

| ファイル | やること / Việc | やらないこと / Không làm |
|---|---|---|
| `models.py` | テーブル定義・リレーション | 業務ロジック / logic nghiệp vụ |
| `serializers.py` | JSONの形の定義・入力検証 | 保存処理・業務判断 / lưu, phán đoán |
| `services.py` | **業務ロジック（純粋な処理）** | HTTP・request を触ること |
| `views.py` | 認可・入力検証・**services 呼び出し**・シリアライズ | 業務ロジックを書くこと |
| `urls.py` | ルーティング登録 | それ以外 |

**依存の向き / Chiều phụ thuộc:** `views` → `services` → `models`
JA: 逆流禁止。`services` は `views`/`request`/`HTTP` を import しない。
VI: Cấm ngược dòng. `services` không import `views`/`request`/`HTTP`.

**なぜこの分離か / Vì sao tách vậy:**
JA: 業務ロジックを `services.py` の純粋関数に閉じ込めると、Django に不慣れなメンバーでも「HTTP を意識せず」
ロジックを書けます。エラーは `apps/common/exceptions.py` のドメイン例外で表し、HTTP への翻訳は例外ハンドラに任せます。
VI: Nhốt logic vào hàm thuần trong `services.py` để người chưa quen Django vẫn viết được logic mà "không cần nghĩ tới HTTP".
Lỗi biểu thị bằng exception nghiệp vụ trong `apps/common/exceptions.py`; dịch sang HTTP giao cho exception handler.

**所有権の絞り込み / Lọc theo chủ sở hữu（厳守 / bắt buộc）:**
JA: 一覧・詳細では **必ず `get_queryset` で `request.user` に絞る**。所有者は入力から受け取らず `request.user` から注入する。
VI: Ở list/detail **luôn lọc theo `request.user` trong `get_queryset`**. Chủ sở hữu không nhận từ đầu vào, mà tiêm từ `request.user`.

JA: `user` を直接持たないモデルもある（例 `KnowledgeNode` の所有者は `topic.user`）。その場合はリレーションを辿って絞る。
VI: Có model không giữ `user` trực tiếp (vd chủ của `KnowledgeNode` là `topic.user`). Khi đó lọc bằng cách đi theo quan hệ.

```python
# 例 / Ví dụ: apps/topics/views.py, apps/reviews/views.py
return KnowledgeNode.objects.filter(topic__user=self.request.user)
return ReviewSchedule.objects.filter(node__topic__user=self.request.user)
```

**エラーの表し方 / Cách biểu thị lỗi:**
JA: `services` は HTTP を知らないので、`apps/common/exceptions.py` のドメイン例外を投げる。`views` で `try/except` して
ステータスを組み立てない（例外ハンドラが翻訳する）。
VI: `services` không biết HTTP nên ném exception nghiệp vụ ở `apps/common/exceptions.py`. Không `try/except` rồi tự dựng
status ở `views` (exception handler sẽ dịch).

| 例外 / Exception | HTTP | 使う場面 / Khi nào dùng |
|---|---|---|
| `ValidationError` | 400 | 入力が不正 / Đầu vào không hợp lệ |
| `PermissionDenied` | 403 | 存在は知ってよいが操作不可 / Được biết là có nhưng không được thao tác |
| `NotFound` | 404 | 対象が無い、**または他人のもの** / Không có, **hoặc của người khác** |

**複数テーブルにまたがる書き込み / Ghi vào nhiều bảng:**
JA: 1つの操作が複数モデルを書き換えるなら `@transaction.atomic` で囲む。途中で失敗したときに
「片方だけできている」中途半端なデータを残さないため。
VI: Nếu một thao tác ghi vào nhiều model thì bọc bằng `@transaction.atomic`, để khi hỏng giữa chừng
không còn lại dữ liệu dở dang kiểu "chỉ xong một nửa".

---

## 2. フロントエンドのレイヤー責務 / Trách nhiệm các tầng frontend

Feature-Sliced 寄せ。依存は上から下への一方向。

```
app/       … Provider・ルーター・レイアウト（最上位の組み立て）
  ↓
pages/     … ルート単位。部品を並べる「組み立て」だけ
  ↓
features/  … 機能ごと（api フック + components）。ここに機能の中身
  ↓
shared/    … api クライアント・共通UI・型・lib（全 feature の土台）
```

**厳守事項 / Bắt buộc:**
1. **HTTP通信は `shared/api/client.ts` 経由のみ。** `fetch` を直接呼ばない。
   / **Giao tiếp HTTP chỉ qua `shared/api/client.ts`.** Không gọi `fetch` trực tiếp.
2. **サーバ状態は TanStack Query。** 自前 `useState`+`useEffect` で取得しない。
   / **Trạng thái server dùng TanStack Query.** Không tự lấy bằng `useState`+`useEffect`.
3. **クエリキーは `shared/api/queryKeys.ts` から取る。** 文字列直書き禁止。
   / **Query key lấy từ `shared/api/queryKeys.ts`.** Cấm viết chuỗi trực tiếp.
4. **`features/` 同士は直接 import しない。** 共有したくなったら `shared/` へ上げる。
   / **Các `features/` không import lẫn nhau.** Muốn dùng chung thì đưa lên `shared/`.
5. **`pages/` は組み立てのみ。** 業務ロジック・通信は `features/` に置く。
   / **`pages/` chỉ lắp ghép.** Logic/giao tiếp đặt ở `features/`.

**なぜ / Vì sao:** JA: 通信・認証・エラー処理を1ファイルに集約すると、5人の実装がブレません。
VI: Gom giao tiếp/auth/xử lý lỗi vào một chỗ giúp code 5 người không lệch nhau.

---

## 3. 命名・ディレクトリ規則 / Quy ước đặt tên & thư mục

- Python: モジュール/関数 `snake_case`、クラス `PascalCase`。import 並び順は `ruff`（isort）に従う。
- TypeScript: コンポーネント/型 `PascalCase`、変数/関数 `camelCase`、フックは `useXxx`。
- 1 feature = 1 フォルダ。`api/`（通信・フック）と `components/`（表示）に分ける。
  変換処理などが増えたら `utils/` を足してよい（例 `features/hintChat/utils/`）。**通信は必ず `api/` 配下に閉じる**。
  / Có thể thêm `utils/` khi có xử lý biến đổi dữ liệu. **Giao tiếp luôn gói trong `api/`**.
- API パス: `/api/<複数形リソース名>/`。語の区切りは**ケバブケース**（例 `/api/chat-sessions/`, `/api/knowledge-nodes/`）。
  認証は `/api/auth/...`。
  / Đường dẫn API: `/api/<tên tài nguyên số nhiều>/`, ngăn cách bằng **kebab-case**.
- ViewSet の追加操作は `@action(url_path="...")` でケバブケース（例 `/api/chat-sessions/{id}/send-message/`）。
  一覧・詳細の形に馴染まない単発の読み取りは `APIView` でよい（例 `/api/learning-tree/`）。
  / Thao tác thêm của ViewSet dùng `@action(url_path=...)` kebab-case. Endpoint đọc đơn lẻ không hợp dạng
  list/detail thì dùng `APIView`.

---

## 4. 新しい Django アプリを追加する手順 / Thêm app Django mới

```bash
cd backend
python manage.py startapp yourapp apps/yourapp   # フォルダを apps/ 配下に作る
```
1. `apps/yourapp/apps.py` の `name` を `"apps.yourapp"` に直す。
2. `config/settings/base.py` の `LOCAL_APPS` に `"apps.yourapp"` を追加。
3. モデルは必要なら `apps/common/models.py` の `BaseModel` を継承（UUID主キー＋時刻）。
4. `services.py` を作り、業務ロジックはそこへ。`views.py` は薄く保つ。
5. `urls.py` で router 登録し、`config/urls.py` に `path("api/", include("apps.yourapp.urls"))` を1行追加。
6. `python manage.py makemigrations yourapp && migrate`。
7. **各ファイル冒頭に「なぜこの責務か」を日本語＋ベトナム語の端的なコメントで書く。**
8. §9 のバックエンドパターンをコピー元にする。
9. `tests.py` に §13 の最低限のテストを書き、`python manage.py test apps` を通す。
   / Viết test tối thiểu theo §13 vào `tests.py` và chạy `python manage.py test apps` cho xanh.
10. 他アプリのデータを使うなら §10、AI を呼ぶなら §11 に従う。
    / Nếu dùng dữ liệu app khác thì theo §10; nếu gọi AI thì theo §11.

---

## 5. 新しいフロント feature を追加する手順 / Thêm feature frontend mới

1. `frontend/src/features/yourfeature/{api,components}/` を作る。
2. `api/hooks.ts` に TanStack Query フックを書く（通信は `shared/api/client.ts` の `api` 経由）。
3. `shared/api/queryKeys.ts` にキーを1グループ追加。
4. `components/` に表示部品。`pages/` で組み立て、`app/router.tsx` にルートを1行追加。
5. §9 のフロントパターンをコピー元にする。

---

## 6. AI コメント規約 / Quy ước comment AI

JA: 各ファイル冒頭に「なぜこの構造・この責務か」を書く。**端的に、日本語＋ベトナム語の2言語**で。
VI: Đầu mỗi file ghi "vì sao cấu trúc/trách nhiệm này". **Ngắn gọn, 2 ngôn ngữ Nhật + Việt.**

**設計を変えたときの書き方 / Khi thay đổi thiết kế:**
JA: 既存の設計を変えたら、変えたファイルの冒頭に `【設計変更 YYYY-MM-DD】` として
**「何を」「なぜ」**を残す。他の4人は変更の経緯を知らないので、コードだけ見ても「前の形に戻す修正」を
してしまうため。フィールドを消したときは、**それを使っていた側（テスト・シリアライザ・フロントの型）も
同じPRで直す**こと。
VI: Khi đổi thiết kế cũ, ghi ở đầu file `【Thay đổi thiết kế YYYY-MM-DD】` kèm **"cái gì" và "vì sao"**.
4 người còn lại không biết bối cảnh, nếu chỉ nhìn code họ dễ "sửa ngược lại như cũ".
Khi xóa field, phải sửa **luôn trong cùng PR** những nơi đang dùng nó (test, serializer, kiểu ở frontend).

---

## 7. Git 運用 / Quy trình Git

- `main` は保護。直接 push しない。作業は `develop` から切ったブランチで行い、**`develop` へ PR**。
  / `main` được bảo vệ, không push thẳng. Làm trên nhánh cắt từ `develop`, **PR vào `develop`**.
- ブランチ名: `feat/<機能>` `fix/<内容>` `chore/<内容>`。
- PR は `.github/PULL_REQUEST_TEMPLATE.md` に従い、**他メンバーへの影響**を必ず記載。
  特に `frontend/src/shared/` 配下（`types/index.ts`・`api/queryKeys.ts`）と**他アプリから参照されている
  services の関数**を変えたときは、影響する feature 名を書く。
  / Nhất là khi sửa `frontend/src/shared/` và **hàm services đang được app khác gọi**, hãy ghi rõ feature bị ảnh hưởng.
- **CI が緑になってからマージ。** CI の中身（`.github/workflows/ci.yml`）:
  / **Merge sau khi CI xanh.** Nội dung CI:

  | 対象 / Phía | 実行内容 / Chạy gì |
  |---|---|
  | backend | `ruff check .` / `ruff format --check .` / `python manage.py makemigrations --check --dry-run` |
  | frontend | `npm run typecheck` / `npm run build` |

- JA: **テストは CI では走らない。** PR を出す前に必ず手元で `cd backend && python manage.py test apps` を通すこと。
  VI: **CI không chạy test.** Trước khi mở PR phải tự chạy `cd backend && python manage.py test apps` cho xanh.

---

## 8. チェックリスト（PR前）/ Checklist (trước PR)

- [ ] §9 のパターンと同じ形になっているか / Có giống pattern §9 không
- [ ] HTTP通信は `client.ts` 経由か / HTTP có qua `client.ts` không
- [ ] 業務ロジックは `services.py` にあるか / Logic có nằm ở `services.py` không
- [ ] `get_queryset` で `request.user` に絞ったか / Đã lọc `request.user` chưa
- [ ] 他アプリのモデルを直接クエリしていないか（§10）/ Không query trực tiếp model của app khác (§10)
- [ ] 表示の値（色など）をバックエンドで決めていないか（§12）/ Không quyết định giá trị hiển thị (màu...) ở backend (§12)
- [ ] クエリキーは `queryKeys.ts` からか / Query key từ `queryKeys.ts` chưa
- [ ] ファイル冒頭に2言語コメントがあるか / Đầu file có comment 2 ngôn ngữ chưa
- [ ] フィールドを消したなら、使っていた側も直したか（§6）/ Nếu xóa field, đã sửa cả nơi đang dùng chưa (§6)
- [ ] `python manage.py test apps` が緑か（§13）/ `python manage.py test apps` có xanh không (§13)
- [ ] CI が緑か / CI có xanh không

---

## 9. 実装パターン（コピー元）/ Pattern hiện thực (nguồn để sao chép)

JA: 以下は「所有者に紐づくリソースの一覧・作成」を全レイヤー貫通で書いた雛形です。`item(s)` / `Item` を
自分のリソース名に置換して使ってください。**この形から外れないこと**が揃えるための条件です。
VI: Dưới đây là khung "liệt kê & tạo tài nguyên gắn với chủ sở hữu" xuyên mọi tầng. Thay `item(s)` / `Item`
bằng tên tài nguyên của bạn. **Không đi chệch hình này** là điều kiện để đồng nhất.

### 9.1 バックエンド / Backend — `apps/items/`

**`models.py`**
```python
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel  # UUID主キー＋created/updated / khóa chính UUID + thời gian


class Item(BaseModel):
    # JA: 所有者。get_queryset で必ず絞る / VI: Chủ sở hữu; luôn lọc trong get_queryset
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name
```

**`serializers.py`**
```python
from rest_framework import serializers

from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "user", "name", "created_at"]
        # JA: user はサーバが決める → read_only / VI: user do server quyết → read_only
        read_only_fields = ["id", "user", "created_at"]
```

**`services.py`** — 業務ロジックはここ（HTTP非依存）/ logic ở đây (không phụ thuộc HTTP)
```python
from apps.common.exceptions import ValidationError
from .models import Item


def create_item(*, user, name: str) -> Item:
    name = (name or "").strip()
    if not name:
        raise ValidationError("名前は必須です / Tên là bắt buộc")
    return Item.objects.create(user=user, name=name)
```

**`views.py`** — 認可・検証・services呼び出し・シリアライズのみ / chỉ phân quyền, kiểm tra, gọi services, tuần tự hóa
```python
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import IsOwner
from . import services
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        # JA: ★所有者絞り込み（必須）/ VI: ★Lọc theo chủ sở hữu (bắt buộc)
        return Item.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # JA: 作成は services へ委譲。所有者は request.user / VI: Tạo ủy thác cho services; chủ sở hữu = request.user
        serializer.instance = services.create_item(
            user=self.request.user,
            name=serializer.validated_data["name"],
        )
```

**`urls.py`**
```python
from rest_framework.routers import DefaultRouter
from .views import ItemViewSet

router = DefaultRouter()
router.register("items", ItemViewSet, basename="item")
urlpatterns = router.urls
```
→ `config/urls.py` に `path("api/", include("apps.items.urls"))` を1行追加。

### 9.2 フロント / Frontend — `features/items/`

**`shared/api/queryKeys.ts`** にキーを追加 / thêm key
```ts
items: {
  all: ['items'] as const,
  list: () => [...queryKeys.items.all, 'list'] as const,
},
```

**`shared/types/index.ts`** に型を追加（バックエンドの出力と一致）/ thêm kiểu (khớp output backend)
```ts
export type Item = { id: string; user: number; name: string; created_at: string }
```

**`features/items/api/hooks.ts`** — 通信は必ず `api` 経由 / giao tiếp luôn qua `api`
```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { Item } from '@/shared/types'

export function useItems() {
  return useQuery({ queryKey: queryKeys.items.list(), queryFn: () => api.get<Item[]>('/items/') })
}

export function useCreateItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: { name: string }) => api.post<Item>('/items/', input),
    // JA: 作成後に list を無効化 → 自動再取得で即反映 / VI: Sau khi tạo, invalidate list → tự lấy lại, phản ánh ngay
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.items.list() }),
  })
}
```

**`features/items/components/ItemList.tsx`** — 読み込み/エラー/空/データの4状態 / 4 trạng thái
```tsx
import { ErrorText, Notice } from '@/shared/ui'
import { useItems } from '../api/hooks'

export function ItemList() {
  const { data, isPending, isError, error } = useItems()
  if (isPending) return <Notice>読み込み中… / Đang tải…</Notice>
  if (isError) return <ErrorText>{(error as Error).message}</ErrorText>
  if (data.length === 0) return <Notice>まだありません / Chưa có</Notice>
  return <ul>{data.map((it) => <li key={it.id}>{it.name}</li>)}</ul>
}
```

**`pages/ItemsPage.tsx`** — 組み立てのみ / chỉ lắp ghép、`app/router.tsx` に保護ルートを1行追加
```tsx
import { RequireAuth } from '@/app/RequireAuth'  // router 側で包む例
// { path: '/items', element: <RequireAuth><ItemsPage /></RequireAuth> }
```

JA: 認証の実装（`apps/accounts/` と `features/auth/`）は削除せず土台として残しています。参考にしてよいですが、
**コピー元は本 §9** を基準にしてください。
VI: Phần xác thực (`apps/accounts/` và `features/auth/`) được giữ làm nền, không xóa. Có thể tham khảo, nhưng
**nguồn sao chép chuẩn là §9 này**.

JA: 自分のアプリだけで完結しない機能（他アプリのデータを使う・AIを呼ぶ）は §10・§11 も見ること。
VI: Tính năng không gói gọn trong app của mình (dùng dữ liệu app khác, gọi AI) thì xem thêm §10, §11.

---

## 10. アプリ間の依存 / Phụ thuộc giữa các app

JA: 5人が別々のアプリを担当するので、**アプリ同士の境界**が一番壊れやすい場所です。
VI: Vì 5 người phụ trách các app khác nhau nên **ranh giới giữa các app** là chỗ dễ vỡ nhất.

**現在の依存 / Phụ thuộc hiện tại:**

```
chat ──→ topics   （ノードの取得・作成 / lấy & tạo node）
chat ──→ reviews  （完了を記録 / ghi nhận hoàn thành）
reviews ──→ topics, chat  （スケジュール対象を辿る / lần theo đối tượng lập lịch）
topics, chat ──→ ai       （LLM 呼び出し / gọi LLM）
すべて ──→ common          （BaseModel・例外・権限 / BaseModel, exception, permission）
```

**厳守事項 / Bắt buộc:**

1. **他アプリのモデルを直接クエリしない。** `OtherModel.objects.filter(...)` を自分のアプリに書かない。
   所有アプリの `services.py` に「窓口関数」を作り、それを呼ぶ。
   / **Không query trực tiếp model của app khác.** Tạo "hàm cửa ngõ" trong `services.py` của app sở hữu và gọi nó.
2. **窓口関数は所有権チェックを内蔵する。** 各アプリが自前で絞り込むと、必ずどこかで忘れる。
   / **Hàm cửa ngõ tự kiểm tra quyền sở hữu.** Nếu mỗi app tự lọc thì thế nào cũng có chỗ quên.
3. **モデルの FK は他アプリを参照してよい**（テーブルの関係そのものなので）。ただし**向きは一方向**にし、
   循環させない。新しい FK を足すときは PR に依存の向きを書く。
   / **FK của model được phép trỏ sang app khác** (đó là quan hệ bảng). Nhưng **giữ một chiều**, không vòng tròn.
4. import が循環しそうなときは、**関数の中で import** してよい。
   / Khi import có nguy cơ vòng tròn, được phép **import bên trong hàm**.

**窓口関数のパターン（所有アプリ側）/ Pattern hàm cửa ngõ (phía app sở hữu)** — `apps/topics/services.py`

```python
def get_owned_knowledge_node(*, user, node_id) -> KnowledgeNode:
    # JA: KnowledgeNode は user を直接持たない（所有者は topic.user）。
    #     各アプリに自前で辿らせると所有権チェックが漏れるので、ここに集約する。
    # VI: KnowledgeNode không giữ user (chủ là topic.user). Để mỗi app tự lần theo sẽ sót
    #     kiểm tra quyền, nên gom về đây.
    node = KnowledgeNode.objects.filter(id=node_id, topic__user=user).first()
    if node is None:
        raise NotFound("KnowledgeNode が見つかりません / Không tìm thấy KnowledgeNode")
    return node
```

**呼ぶ側 / Phía gọi** — `apps/chat/services.py`

```python
def create_chat_session_for_node(*, user, node_id=None, title="New Session"):
    # JA: 循環 import を避けるため関数内 import。VI: Import trong hàm để tránh vòng tròn.
    from apps.topics import services as topics_services

    node = topics_services.get_owned_knowledge_node(user=user, node_id=node_id) if node_id else None
    ...
```

JA: ✗ 悪い例: `KnowledgeNode.objects.filter(id=node_id).first()` … 所有者を条件に入れ忘れると、
**他人のデータに自分のレコードを紐付けられてしまう**。
VI: ✗ Ví dụ sai: `KnowledgeNode.objects.filter(id=node_id).first()` … quên điều kiện chủ sở hữu thì
**có thể gắn bản ghi của mình vào dữ liệu của người khác**.

---

## 11. AI（LLM）の呼び方 / Cách gọi AI (LLM)

1. **必ず `apps/ai` の `get_llm()` 経由。** `services.py` から SDK（`google.generativeai` 等）を直接呼ばない。
   / **Luôn qua `get_llm()` của `apps/ai`.** Không gọi thẳng SDK từ `services.py`.
2. **既定は `AI_PROVIDER=fake`。** APIキーが無くても開発・テストできる。テストでも fake を使う。
   / **Mặc định `AI_PROVIDER=fake`**, không cần API key vẫn phát triển/test được.
3. **プロンプトは `services.py` のモジュール定数**にまとめる（関数の中に文字列を埋めない）。
   / **Prompt gom thành hằng số ở đầu `services.py`**, không nhúng chuỗi trong hàm.
4. **AI の失敗でリクエストを落とさない。** 例外を捕まえてログを残し、代替の応答を返す。
   / **Không để lỗi AI làm hỏng request.** Bắt exception, ghi log, trả về phản hồi thay thế.
5. **AI の出力形式は緩く受ける。** 「1行目=タイトル、2行目以降=本文」のように単純な規約にし、パースは防御的に。
   / **Nhận đầu ra của AI một cách nới lỏng.** Quy ước đơn giản (dòng 1 = tiêu đề...), parse phòng thủ.

```python
from apps.ai.base import ChatMessage as AIChatMessage
from apps.ai.client import get_llm

llm = get_llm()
result = llm.chat([
    AIChatMessage(role="system", content=SYSTEM_PROMPT),
    AIChatMessage(role="user", content=text),
])
result.text  # ChatResult
```

---

## 12. バックエンドとフロントの責務境界 / Ranh giới trách nhiệm backend - frontend

JA: 「見た目をどう決めるか」はフロントの責務です。バックエンドは**判断の材料**を返します。
VI: "Quyết định hiển thị thế nào" là việc của frontend. Backend trả về **nguyên liệu để quyết định**.

| バックエンドが返すもの / Backend trả | フロントが決めるもの / Frontend quyết |
|---|---|
| 数値・フラグ・閾値（`mastery_level`, `is_due`, `mastery_max_level`） | 色・濃さ・バッジ・文言 / màu, độ đậm, badge, chữ |

JA: ✗ 悪い例: API が `"#2E7D46"` のような色コードを返す。デザインを変えるたびにバックエンドの修正と
デプロイが要る上、同じ値を使う別画面と食い違う。
VI: ✗ Ví dụ sai: API trả mã màu như `"#2E7D46"`. Mỗi lần đổi thiết kế phải sửa và deploy backend,
lại dễ lệch với màn hình khác dùng cùng giá trị.

**画面用の集計をどこでやるか / Tính toán tổng hợp ở đâu:**
JA: フロントが**すでに取得している2つのAPIを突き合わせれば出せる**ものは、フロントで計算する
（例: 木全体の定着率 = `/learning-tree/` の葉と `/review-schedules/` を `node_id` で突き合わせる）。
そのためだけの集計APIを増やさない。行数が多くて重い、または複数画面で使い回す段階になったら
バックエンドに移す。
VI: Nếu **ghép 2 API frontend đã lấy sẵn là ra được** thì tính ở frontend (vd: tỉ lệ ghi nhớ của cây).
Không thêm API tổng hợp chỉ để làm việc đó. Khi dữ liệu lớn/nặng hoặc nhiều màn hình cùng dùng thì mới chuyển về backend.

---

## 13. テスト / Test

JA: CI では走らないので、**PR前に必ず手元で** `cd backend && python manage.py test apps` を通します。
VI: CI không chạy test, nên **trước khi mở PR bắt buộc** chạy `cd backend && python manage.py test apps`.

**最低限これは書く / Tối thiểu phải có:**

1. 正常系を1本（機能の主要フローが通ること）/ 1 test luồng chính chạy được
2. **所有権**（他人のデータが見えない・触れない → 404 か空リスト）/ **Quyền sở hữu** (không thấy/không chạm được dữ liệu người khác)
3. **回帰**（バグを直したら、同じバグを再現するテストを1本残す）/ **Hồi quy** (sửa bug thì để lại 1 test tái hiện bug đó)

**書き方 / Cách viết:**

- `django.test.TestCase` ＋ `self.client.force_login(user)`。テスト用DBは自動で作られる。
  / Dùng `TestCase` + `force_login`. DB test được tạo tự động.
- AI を使う経路は `AI_PROVIDER=fake` のまま実行する（外部APIを叩かない）。
  / Đường đi có AI thì để `AI_PROVIDER=fake` (không gọi API ngoài).
- **他アプリの API 越しにテストしない。** 自分のアプリの `services` を直接呼ぶ。
  他アプリの担当がAPIの形を変えても、自分のテストが巻き添えで壊れないようにするため。
  / **Không test xuyên qua API của app khác.** Gọi thẳng `services` của app mình, để khi app khác đổi API
  thì test của mình không vỡ lây.
- テストがモデルの変更に追従できていないと**全件エラーになる**（`setUp` が落ちるため）。
  フィールドを消したら `tests.py` も同じPRで直す（§6）。
  / Nếu test không theo kịp thay đổi model thì **toàn bộ test lỗi** (do `setUp` hỏng). Xóa field thì sửa `tests.py` trong cùng PR.

---

## 14. マイグレーション / Migration

1. **モデルを変えたら必ず `makemigrations`。** CI が `--check` で漏れを検出する。
   / **Đổi model là phải `makemigrations`.** CI phát hiện thiếu bằng `--check`.
2. `@property` の追加・削除、コメント変更では**マイグレーションは不要**（DBの列は変わらない）。
   / Thêm/xóa `@property` hay sửa comment thì **không cần migration**.
3. **1つのPRのマイグレーションは、できるだけ1本にまとめる。** 作業途中で何本もできたら、消して作り直す。
   / **Gộp migration của 1 PR thành 1 file nếu được.** Nếu lỡ tạo nhiều thì xóa và tạo lại.
4. **PR前に `develop` を取り込む。** 別々のブランチで同じアプリのマイグレーションが増えると、
   親（`dependencies`）が枝分かれして壊れる。分かれてしまったら `makemigrations --merge` で合流させる。
   / **Merge `develop` vào trước khi mở PR.** Hai nhánh cùng thêm migration cho một app sẽ làm nhánh
   `dependencies` chẻ đôi; nếu đã chẻ thì hợp lại bằng `makemigrations --merge`.
5. **他人が作ったマイグレーションを書き換えない。** 適用済みの環境が壊れる。直したいときは新しい1本を足す。
   / **Không sửa migration của người khác** (làm hỏng môi trường đã apply). Muốn sửa thì thêm file mới.
