# 間隔復習機能 API仕様(reviews)

対象: `backend/apps/reviews/` が提供するエンドポイント。フロント連携のすり合わせ用。

## 前提

- 認証はセッション認証(JWTではない)。ログイン・CSRF取得は `apps/accounts` 側の
  `/api/auth/csrf/` `/api/auth/login/` `/api/auth/me/` を使う前提で、reviews側は
  それらが済んでいる(`request.user` が取れる)ことを前提にしている。
- `/api` はViteが `:8000` にプロキシする(同一オリジン化)ので、CSRFトークンの
  やり取りは `shared/api/client.ts` の既存実装に乗ればよく、reviews用に特別な
  処理は不要。
- 全エンドポイント、未ログイン時は `401`(DRFのデフォルト、`IsAuthenticated`)。

---

## GET /api/review-schedules/due/

復習タイミングが来ている(`next_review_at <= 現在時刻`)ノードの一覧。`request.user`
が所有するTopic配下のものだけを返す。

**リクエスト**: パラメータなし。

**レスポンス 200**

```json
[
  {
    "id": "5f2c...",              // ReviewScheduleのid
    "node_id": "9a1e...",         // KnowledgeNodeのid(常設ノード)
    "node_title": "現在完了形の基本",
    "topic_id": "3b7d...",
    "interval_days": 6,
    "next_review_at": "2026-08-10T09:00:00Z",
    "learned_count": 3,
    "retention_level": "overdue", // "unlearned" | "fresh" | "fading" | "overdue"
    "retention_color": "#C9622A"  // 木の表示にそのまま使える16進カラー
  }
]
```

空配列 `[]` は「今復習すべきものが無い」を意味する(エラーではない)。

---

## POST /api/review-schedules/start/

選んだノードで復習を開始する。AIが類題を生成し、対話機能側で`Attempt`・
`ChatSession`を作成した結果を返す。

**リクエスト**

```json
{ "node_id": "9a1e..." }
```

`node_id` は `due` 一覧の `node_id`(常設ノード側)を渡す。

**レスポンス 201**

```json
{
  "attempt_id": "c4e1...",
  "chat_session_id": "7d90..."
}
```

フロントはこれを受け取ったら、チャット画面(`features/learning` 側)に
`chat_session_id` を渡して遷移する想定。

**エラー時の形が2種類ある(要注意)**

| ケース | ステータス | ボディ | 理由 |
|---|---|---|---|
| `node_id` が無い・UUID形式が不正・存在しないノード | `400` | `{"node_id": ["KnowledgeNode not found"]}` | シリアライザのバリデーションエラー(DRF標準形式、フィールド名がキーになる) |
| `node_id` は存在するが自分のものではない | `404` | `{"detail": "KnowledgeNode not found"}` | `apps.common.exceptions` のドメイン例外(共通の`{"detail": ...}`形式) |

同じ「見つからない」でも、シリアライザ側で弾かれた場合とビュー内の所有者チェックで
弾かれた場合とでレスポンスの形が違う。フロント側でエラー表示を出す際は、
`error.node_id?.[0] ?? error.detail` のように両対応にしておくと安全。

---

## フロント側の実装イメージ(CONVENTIONS.md §9パターンに沿う場合)

`features/reviews/api/queryKeys.ts` への追加案:

```ts
reviews: {
  all: ['review-schedules'] as const,
  due: () => [...queryKeys.reviews.all, 'due'] as const,
},
```

`features/reviews/api/hooks.ts` の案:

```ts
export function useDueReviews() {
  return useQuery({
    queryKey: queryKeys.reviews.due(),
    queryFn: () => api.get<ReviewSchedule[]>('/review-schedules/due/'),
  })
}

export function useStartReview() {
  return useMutation({
    mutationFn: (input: { nodeId: string }) =>
      api.post<{ attempt_id: string; chat_session_id: string }>(
        '/review-schedules/start/',
        { node_id: input.nodeId },
      ),
  })
}
```

`shared/types/index.ts` に足す型の案(既存の `StepNode` とは別物として):

```ts
export type ReviewSchedule = {
  id: string
  node_id: string
  node_title: string
  topic_id: string
  interval_days: number
  next_review_at: string
  learned_count: number
  retention_level: 'unlearned' | 'fresh' | 'fading' | 'overdue'
  retention_color: string
}
```

---

## まだ決まっていないこと

- `apps.topics` 側の検索セッション用エンドポイント(カテゴリツリーから復習範囲を
  選ぶUI向け)は、reviewsのAPIとは別に用意される想定。今回のドキュメントには含めていない。
- 復習を「しない」を選んだ場合のAPI(何もしない=呼ばなくてよい)なので、
  こちらにエンドポイントは無い。フロント側は単にモーダルを閉じるだけでよい。
