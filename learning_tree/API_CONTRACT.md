# 学習木構造 API仕様(topics)

対象: `backend/apps/topics/` が提供するエンドポイント。フロント連携のすり合わせ用。
ブランチ: `feat/learning-tree-api`(develop起点、未マージ)。

## 前提

- 認証はセッション認証(JWTではない)。ログイン・CSRF取得は `apps/accounts` 側の
  `/api/auth/csrf/` `/api/auth/login/` `/api/auth/me/` を使う前提で、topics側は
  それらが済んでいる(`request.user` が取れる)ことを前提にしている。
- `/api` はViteが `:8000` にプロキシする(同一オリジン化)ので、CSRFトークンの
  やり取りは `shared/api/client.ts` の既存実装に乗ればよく、topics用に特別な
  処理は不要。
- 全エンドポイント、未ログイン時は `401`(DRFのデフォルト、`IsAuthenticated`)。
- 一覧・作成すべてで `request.user` に所有権を絞り込む(他人のTopic/KnowledgeNodeは
  見えない・触れない)。

---

## モデルの前提

| モデル | 例え | 主なフィールド |
|---|---|---|
| `Topic` | 本棚の「棚」(カテゴリ) | `user`, `parent`(自己参照,nullable), `name`, `description`, `position` |
| `KnowledgeNode` | 棚に並ぶ「本」(実際に学んだ内容) | `topic`, `origin_node`(自己参照,nullable), `title`, `content` |

- `origin_node` が入っている `KnowledgeNode` は、間隔復習機能(`apps/reviews`)がAIに
  生成させた使い捨ての類題。**学習木構造のツリーには含まれない**(常設ノードのみ表示)。
- `KnowledgeNode` の構造(topic/origin_node/title/content)への書き込みは
  `apps/topics/services.py` に一本化している。他アプリ(`apps/reviews`)が類題を
  作る際も `services.create_derived_node()` を経由する(直接 `.objects.create()` しない)。
  この関数はREST化されていない、Pythonレベルの内部API。

---

## GET /api/learning-tree/

`request.user` が持つ Topic階層 + 各Topicに属する KnowledgeNode(常設ノードのみ)を、
入れ子のツリー形式で1回で取得する。フロントの `TreeNode` 型と対応。

**リクエスト**: パラメータなし。

**レスポンス 200**

```json
[
  {
    "id": "3b7d...",
    "label": "数学",
    "type": "topic",
    "children": [
      {
        "id": "8c1a...",
        "label": "代数",
        "type": "topic",
        "children": [
          { "id": "9a1e...", "label": "一次方程式の基礎", "type": "knowledge_node" }
        ]
      }
    ]
  }
]
```

- `type: "topic"` は棚(カテゴリ)、`type: "knowledge_node"` は本(実際に学んだ内容)。
  復習開始(`POST /api/review-schedules/start/`、`review_api/API_CONTRACT.md` 参照)に
  渡せる `node_id` は `type: "knowledge_node"` のノードの `id` のみ。
- `children` は子が1件も無いノードには含まれない(空配列ではなくキー自体が無い)。
- 空配列 `[]` は「まだTopicを1つも作っていない」を意味する(エラーではない)。
- 兄弟の並び順: `Topic` は `position` 昇順→`created_at`、`KnowledgeNode` は `created_at` 昇順
  (`position` 相当のフィールドを持たない)。

---

## GET/POST /api/topics/

**GET** 一覧(`request.user` のTopicのみ、フラットな配列。木構造ではない)。

**レスポンス 200**

```json
[
  {
    "id": "3b7d...",
    "user": 1,
    "parent": null,
    "name": "数学",
    "description": "",
    "position": 0,
    "created_at": "2026-08-12T09:00:00Z"
  }
]
```

**POST** 新しいTopicを作成。

**リクエスト**

```json
{ "name": "代数", "description": "", "parent": "3b7d..." }
```

- `parent` は省略可(省略/`null`でルートTopicになる)。
- `user` / `position` はサーバ側が決めるため送っても無視される(`read_only`)。
  `position` は同じ親を持つ兄弟の末尾番号が自動採番される。

**レスポンス 201**: 作成された Topic オブジェクト(GETと同じ形)。

**エラー**

| ケース | ステータス | ボディ |
|---|---|---|
| `name` が空 | `400` | `{"name": ["This field may not be blank."]}` |
| `parent` が他人のTopic | `403` | `{"detail": "他人のTopic配下には作成できません / Không thể tạo dưới Topic của người khác"}` |
| `parent` のUUIDが存在しない | `400` | `{"parent": ["無効な主キーです..."]}`(DRF標準) |

---

## GET/POST /api/knowledge-nodes/

**GET** 一覧(`request.user` のTopicに属するKnowledgeNodeのみ。類題ノードも含む)。

**レスポンス 200**

```json
[
  {
    "id": "9a1e...",
    "topic": "8c1a...",
    "origin_node": null,
    "title": "一次方程式の基礎",
    "content": "x + 3 = 7 を解け",
    "created_at": "2026-08-12T09:05:00Z"
  }
]
```

**POST** 新しいKnowledgeNodeを作成(常設ノードのみ。類題は `create_derived_node` 経由でreviews機能が作る)。

**リクエスト**

```json
{ "topic": "8c1a...", "title": "一次方程式の基礎", "content": "x + 3 = 7 を解け" }
```

- `origin_node` はサーバ側専用(`read_only`)。ユーザーが直接指定することはできない。

**レスポンス 201**: 作成された KnowledgeNode オブジェクト(GETと同じ形)。

**エラー**

| ケース | ステータス | ボディ |
|---|---|---|
| `title` が空 | `400` | `{"title": ["This field may not be blank."]}` |
| `topic` が他人のTopic | `403` | `{"detail": "他人のTopicには追加できません / Không thể thêm vào Topic của người khác"}` |

---

## フロント側の実装(実装済み)

`shared/types/index.ts`

```ts
export type TreeNode = {
  id: string
  label: string
  type: 'topic' | 'knowledge_node'
  children?: TreeNode[]
}
```

`features/learningTree/api/hooks.ts`

```ts
export function useLearningTree() {
  return useQuery({
    queryKey: queryKeys.learningTree.list(),
    queryFn: () => api.get<TreeNode[]>('/learning-tree/'),
  })
}
```

`/api/topics/` `/api/knowledge-nodes/` に対応するフロントフック(作成フォーム等)は
今回未実装(下記「まだ決まっていないこと」参照)。

---

## まだ決まっていないこと

- `Topic` / `KnowledgeNode` の更新(PATCH)・削除(DELETE)・並び替え(`position`変更)の
  エンドポイントは未実装(今回は一覧・作成のみ)。
- フロント側の作成フォーム・並び替えUI・「木の葉(knowledge_node)をクリックして復習を
  始める」導線(`review_api/API_CONTRACT.md` の `POST /api/review-schedules/start/` へ
  つなぐ部分)は未実装。
- `Topic`/`KnowledgeNode`が実際にどう増えていくか(チャット機能でAIと学んだ内容を
  自動でノード化するのか、手動作成のみか)は未確定。現状は上記POSTエンドポイントで
  手動作成のみ可能。
- `apps/reviews` は `LOCAL_APPS` に未登録・マイグレーション未生成のままなので、
  `review_api/API_CONTRACT.md` に書かれているエンドポイントは現時点でまだ動かない
  (今回のtopics実装とは別タスク)。
