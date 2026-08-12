# 検索セッション(topics) — フロント連携ガイド / Hướng dẫn tích hợp frontend

JA: `apps/topics`が提供するAPIの実際の使い方です。仕様の詳細は同フォルダの
    `API_CONTRACT.md`を見てください。
VI: Cách sử dụng thực tế API do `apps/topics` cung cấp. Chi tiết đặc tả xem
    `API_CONTRACT.md` trong cùng thư mục.

---

## 1. 画面の流れ / Luồng màn hình

1. JA: ルートトピック一覧を表示し、ユーザーが1つ選ぶ
   VI: Hiển thị danh sách Topic gốc, người dùng chọn 1 cái
2. JA: 選んだトピックの配下(子トピック・課題)を表示する
   VI: Hiển thị dữ liệu con của Topic đã chọn (Topic con, bài toán)
3. JA: 任意でキーワード検索を行う(配下を再帰的に検索)
   VI: Tùy chọn tìm theo từ khóa (tìm đệ quy trong phạm vi đã chọn)
4. JA: 課題を1件選ぶと詳細画面へ。そこから対話機能(チャット)を開始できる
   VI: Chọn 1 bài toán để vào màn hình chi tiết. Từ đó có thể bắt đầu tính năng đối thoại (chat)

---

## 2. 実際の呼び方 / Cách gọi thực tế

### ルートトピック一覧 / Danh sách Topic gốc

```ts
// features/search/api/hooks.ts
import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { queryKeys } from '@/shared/api/queryKeys'
import type { Topic } from '@/shared/types'

export function useRootTopics() {
  return useQuery({
    queryKey: queryKeys.topics.roots(),
    queryFn: () => api.get<Topic[]>('/topics/?parent=null'),
  })
}
```

### 配下の取得(ドリルダウン) / Lấy dữ liệu con (duyệt sâu dần)

```ts
type TopicChildren = { topics: Topic[]; nodes: KnowledgeNodeSummary[] }

export function useTopicChildren(topicId: string) {
  return useQuery({
    queryKey: queryKeys.topics.children(topicId),
    queryFn: () => api.get<TopicChildren>(`/topics/${topicId}/children/`),
    enabled: !!topicId,
  })
}
```

JA: `topics`(子トピック)と`nodes`(課題)が同時に返るので、画面では
    フォルダアイコン(トピック)とファイルアイコン(課題)のように
    並べて表示するイメージです。
VI: `topics` (Topic con) và `nodes` (bài toán) trả về cùng lúc, nên ở màn hình
    có thể hiển thị như icon thư mục (topic) và icon file (bài toán) xen kẽ nhau.

### キーワード検索 / Tìm theo từ khóa

```ts
export function useTopicSearch(topicId: string, query: string) {
  return useQuery({
    queryKey: queryKeys.topics.search(topicId, query),
    queryFn: () =>
      api.get<KnowledgeNodeSummary[]>(
        `/topics/${topicId}/search/?q=${encodeURIComponent(query)}`,
      ),
    enabled: !!topicId && query.length > 0, // JA: 空文字では呼ばない / VI: Không gọi khi rỗng
  })
}
```

JA: `q`が空だとサーバー側が`400`を返すので、フロント側でも`query.length > 0`の
    ときだけ呼ぶようにしてください(上の`enabled`がそれです)。
VI: Nếu `q` rỗng thì server trả về `400`, nên phía frontend cũng chỉ gọi khi
    `query.length > 0` (chính là `enabled` ở trên).

### 課題の詳細 / Chi tiết bài toán

```ts
export function useKnowledgeNode(nodeId: string) {
  return useQuery({
    queryKey: queryKeys.topics.node(nodeId),
    queryFn: () => api.get<KnowledgeNodeDetail>(`/knowledge-nodes/${nodeId}/`),
    enabled: !!nodeId,
  })
}
```

JA: ここで取得した`id`を使って、対話機能側の「挑戦を開始する」APIを呼べば
    チャット画面に進めます(そちらは`apps/learning`担当のエンドポイントです)。
VI: Dùng `id` lấy được ở đây để gọi API "bắt đầu thử thách" của tính năng đối
    thoại, sẽ chuyển sang màn hình chat (đó là endpoint của `apps/learning`).

---

## 3. queryKeys.ts への追加案 / Đề xuất thêm vào queryKeys.ts

```ts
topics: {
  all: ['topics'] as const,
  roots: () => [...queryKeys.topics.all, 'roots'] as const,
  children: (topicId: string) => [...queryKeys.topics.all, 'children', topicId] as const,
  search: (topicId: string, q: string) => [...queryKeys.topics.all, 'search', topicId, q] as const,
  node: (nodeId: string) => [...queryKeys.topics.all, 'node', nodeId] as const,
},
```

## 4. shared/types/index.ts への追加案 / Đề xuất thêm vào shared/types/index.ts

```ts
export type Topic = {
  id: string
  name: string
  description: string
  position: number
  parent: string | null
  has_children: boolean
}

export type KnowledgeNodeSummary = {
  id: string
  title: string
  topic: string
}

export type KnowledgeNodeDetail = {
  id: string
  title: string
  content: string
  topic: string
  topic_name: string
}
```

---

質問があれば気軽に聞いてください。/ Có thắc mắc gì cứ hỏi thoải mái.
