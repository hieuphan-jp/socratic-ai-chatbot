# 検索セッション API仕様(topics)

対象: `backend/apps/topics/` が提供するエンドポイント。フロント連携のすり合わせ用。

## 前提

- 認証は`apps/accounts`のセッション認証にそのまま乗る。`reviews`と同じ扱い。
- 全エンドポイント、未ログイン時は`401`。
- 「AI生成の使い捨て類題」(`origin_node`を持つKnowledgeNode)は、一覧にも
  検索結果にも出てこない。検索セッションで見せるのは常設の課題だけ。
- `retention_color`(記憶定着の色)はここでは返さない。木の色分けが必要な
  場合は`reviews`側のAPI(`GET /api/review-schedules/due/`など)と組み合わせる。

---

## GET /api/topics/?parent=null

ルートトピック(検索セッションの起点)一覧。`request.user`が所有するものだけ。

**クエリパラメータ**: `parent=null` を付けるとルートのみ。付けない場合は
全トピックがフラットに返る(通常は`parent=null`を使う想定)。

**レスポンス 200**

```json
[
  {
    "id": "3b7d...",
    "name": "英文法",
    "description": "",
    "position": 0,
    "parent": null,
    "has_children": true
  }
]
```

---

## GET /api/topics/{id}/children/

指定トピックの直下(子トピック・このトピックに直属するKnowledgeNode)を取得する。
ドリルダウンUI用。

**レスポンス 200**

```json
{
  "topics": [
    { "id": "...", "name": "現在完了形", "description": "", "position": 0, "parent": "3b7d...", "has_children": false }
  ],
  "nodes": [
    { "id": "9a1e...", "title": "現在完了形の基本", "topic": "3b7d..." }
  ]
}
```

**エラー**: 自分のトピックでない`id`を指定した場合は`404` `{"detail": "..."}`。

---

## GET /api/topics/{id}/search/?q=キーワード

指定トピック配下(自身を含む)を**再帰的に**検索し、`title`または`content`に
キーワードを含むKnowledgeNodeを返す。子トピック自体は結果に含まれない
(あくまでKnowledgeNodeの検索)。

**レスポンス 200**: `children`の`nodes`と同じ形の配列。

**エラー**: `q`が空の場合 `400` `{"detail": "q is required"}`。

---

## GET /api/knowledge-nodes/{id}/

課題の詳細。検索結果や配下一覧から1件選んだときに呼ぶ。

**レスポンス 200**

```json
{
  "id": "9a1e...",
  "title": "現在完了形の基本",
  "content": "次の英文を現在完了形に書き換えなさい。...",
  "topic": "3b7d...",
  "topic_name": "英文法"
}
```

**エラー**: 自分のノードでない場合は`404`。

---

## この先(スコープ外)

- 選んだ課題で「挑戦を開始する」のは`reviews`とは別で、対話機能
  (`apps/learning`)側のエンドポイントを直接呼ぶ想定。`topics`側には
  それをラップするAPIは用意していない(単純に`node_id`を渡すだけなので、
  ラップする理由が無いため)。
