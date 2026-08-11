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
- 1 feature = 1 フォルダ。`api/`（フック）と `components/`（表示）に分ける。
- API パス: `/api/<複数形リソース名>/`（例 `/api/items/`）。認証は `/api/auth/...`。

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

---

## 7. Git 運用 / Quy trình Git

- `main` は保護。直接 push しない。作業は `develop` から切ったブランチで行い、**`develop` へ PR**。
  / `main` được bảo vệ, không push thẳng. Làm trên nhánh cắt từ `develop`, **PR vào `develop`**.
- ブランチ名: `feat/<機能>` `fix/<内容>` `chore/<内容>`。
- PR は `.github/PULL_REQUEST_TEMPLATE.md` に従い、**他メンバーへの影響**を必ず記載。
- **CI（ruff / typecheck / build）が緑になってからマージ。**

---

## 8. チェックリスト（PR前）/ Checklist (trước PR)

- [ ] §9 のパターンと同じ形になっているか / Có giống pattern §9 không
- [ ] HTTP通信は `client.ts` 経由か / HTTP có qua `client.ts` không
- [ ] 業務ロジックは `services.py` にあるか / Logic có nằm ở `services.py` không
- [ ] `get_queryset` で `request.user` に絞ったか / Đã lọc `request.user` chưa
- [ ] クエリキーは `queryKeys.ts` からか / Query key từ `queryKeys.ts` chưa
- [ ] ファイル冒頭に2言語コメントがあるか / Đầu file có comment 2 ngôn ngữ chưa
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
