# チャット機能マージ後の再確認リスト / Checklist sau khi merge nhánh Chat

> **この文書の目的**
> 学習木構造・復習スケジューリングの目標フロー（後述のパターン1・2）が現行バックエンドで成立するかを
> 2026-08-15 に検証した結果、**チャット機能（`backend/apps/chat/`）の既存実装を変更しないと直せない問題**が
> 見つかりました。チャット機能は別ブランチで改修中のため、それらはこのブランチでは手を付けていません。
>
> チャット機能ブランチを `develop` にマージした直後に、この文書の項目を上から順に確認してください。
> **すでに解決されている項目もあるはずです**（「解決済みか」の欄をチェックしていく使い方を想定）。
>
> ベトナム語版: `CHAT_MERGE_FOLLOWUP.vi.md`

---

## 0. 前提：目標とするデータの流れ

### パターン1：初めて学ぶ内容

1. チャット開始 → `ChatSession` が1件できる（`Attempt` と `KnowledgeNode` はまだ無い）
2. ユーザーが「学習達成ボタン」を押す（このときトピックの選択／新規作成も行う）
3. 2 の瞬間に `KnowledgeNode` と `Attempt` が1件ずつできる
   - `KnowledgeNode` ↔ `ChatSession` は **1対1**
   - `Attempt` は **初回学習・以降の復習ごとに毎回** 作られる

### パターン2：2回目以降の復習

1. 復習回数（定着度）に応じて葉の緑が濃くなり、復習予定日を過ぎた葉には別UIで合図が出る
2. ユーザーは合図の出ている葉を選ぶ
3. その葉に対応する過去のチャットセッションに入り直せる
4. 会話を読み返す／続きを話す
5. 「復習達成ボタン」で `Attempt` に完了時刻が入り、次回の復習日が更新される
   （**ボタンが押されるまで `Attempt` は作られない**）
6. 葉の色と、木全体の定着率（％）が更新される

### 決定済みの設計方針（2026-08-15）

| 記号 | 決定 |
|---|---|
| A | `hint_count` は用途が無くなったので**廃止**。`Attempt` は**完了時のみ**作成する |
| B | 葉の色は**フロントが** `/api/learning-tree/` と `/api/review-schedules/` を `node_id` で突き合わせて決める（バックエンドに集計APIは作らない） |
| C | **緑の濃さ＝復習回数（定着度）**、**復習タイミング＝緑とは別のUI**。木全体の定着率(%) = 「予定日をまだ過ぎていない葉 ÷ 木の葉の総数」 |
| D | 理解度の自己申告は**しない**。「予定日に自分でノードを見に行き完了ボタンを押した」ことだけで計算する（将来もっと柔軟な方式に差し替える余地は残す） |
| F | コピー＆ペースト禁止はフロント側の実装で対応（バックエンドの対応は当面不要） |

---

## 1. このブランチ（`feat/learning-tree-retention-api`）で対応済み

チャット機能に触れずに済んだものは対応しました。マージ後にやり直す必要はありません。

| 内容 | 場所 |
|---|---|
| 他アプリ向けの所有権チェック窓口 `get_owned_knowledge_node()` を追加（後述 2-2 で使う） | `apps/topics/services.py` |
| `retention_level` / `retention_color`（1軸4段階）を廃止し、**`mastery_level`（緑の濃さ）＋ `is_due` / `days_overdue`（復習の合図）の2軸**に変更（決定C） | `apps/reviews/models.py`, `serializers.py` |
| 色コード（16進）をバックエンドが返すのをやめ、フロントで決める形に変更 | 同上 |
| 理解度の自己申告を廃止し、完了は固定評価で記録（決定D）。`record_review_result(attempt, understood)` の `understood` は**受け取るが無視する**（チャット側がまだ渡してくるため） | `apps/reviews/services.py` |
| `due` 一覧を「放置が長い順」に並べ替え | `apps/reviews/views.py` |
| `origin_node` 削除に追従できておらず **17件すべてがエラーだった topics のテストを修復** | `apps/topics/tests.py` |
| 復習スケジューリングのテストを新規追加（9件） | `apps/reviews/tests.py` |

---

## 2. チャット機能側に残した項目（要対応）

### 2-1. 【最優先・ブロッカー】達成ボタンが 400 で弾かれる

- **症状**：本文を入力せずに達成ボタンだけ押すと、パターン1-2/1-3 が完走できない。

  ```
  POST /api/chat-sessions/{id}/send-message/
  {"action_type": "COMPLETE", "topic_id": "..."}
  → 400 {"message_text": ["This field is required."]}

  {"message_text": "", "action_type": "COMPLETE", "topic_id": "..."}
  → 400 {"message_text": ["This field may not be blank."]}
  ```

- **原因**：`apps/chat/serializers.py` の `SendMessageInputSerializer.message_text` が `required=True`。
  一方 `apps/chat/services.py` の `send_message_and_get_ai_response()` は空文字を許す作り
  （必須なのは `ANSWER` / `REQUEST_CHANGE_METHOD` のときだけ）で、**シリアライザ側だけ不整合**。
- **暫定回避の危険**：フロントからダミー文字列を送ると、それが**本物の発言としてDBに保存され**、
  会話履歴とグラフに残ります（さらに 2-5 の種別問題も踏みます）。
- **推奨する直し方**：達成ボタンを会話送信APIから分離する。

  ```
  POST /api/chat-sessions/{id}/complete/      ← 本文不要。topic_id は初回のみ
  POST /api/chat-sessions/{id}/send-message/  ← 純粋に会話だけ
  ```

  これで本問題は構造的に消え、達成ボタンが会話履歴を汚さなくなります。
  分離しない場合は最低限 `required=False, allow_blank=True, default=""` にすること。
- **解決済みか**：☐

### 2-2. 【セキュリティ】他人の KnowledgeNode に自分のセッションを紐付けられる

- **症状**：他ユーザーの `node_id` を渡してセッションを作ると、

  - そのノードに既存セッションがある場合 → `UNIQUE constraint failed: chat_chatsession.knowledge_node_id` で **500**
  - 無い場合 → **他人のノードに自分のセッションが紐付き、以降の完了操作で他人の復習スケジュールを書き換えられる**

- **原因**：`apps/chat/services.py` の `create_chat_session_for_node()` が
  `KnowledgeNode.objects.filter(id=node_id)` と、**所有者を条件に入れずに検索**している。
  `KnowledgeNode` は `user` を直接持たず `topic.user` が所有者なので、各アプリで自前検索すると漏れます。
- **CLAUDE.md 違反**：レビュー必須チェック項目3「他アプリが所有するモデルへの直接ORMアクセス」に該当。
- **直し方**：このブランチで用意済みの窓口に差し替えるだけです。

  ```python
  from apps.topics import services as topics_services

  node = topics_services.get_owned_knowledge_node(user=user, node_id=node_id)
  # 見つからない/他人のもの → NotFound (404) が飛ぶ
  ```

  （`get_owned_topic()` と同じ形。所有権チェック付きで、テストも `apps/topics/tests.py` にあります）
- **解決済みか**：☐

### 2-3. 【整合性】完了処理がトランザクションで囲われていない

- **症状**：完了時は「`KnowledgeNode` 作成 → `Attempt` 完了 → `ReviewLog` 記録 → 次回日程更新」が
  順に走りますが、それぞれ別コミットです。途中で失敗すると
  **「ノードはあるのに復習スケジュールが無い」**中途半端な状態が残ります。
- **直し方**：完了処理の入口に `@transaction.atomic` を1つ付ける。
- **解決済みか**：☐

### 2-4. 【決定A】`Attempt.hint_count` の廃止と、Attempt の生成タイミング

- **現状**：ヒント押下でも `Attempt` が作られます（`get_or_create_active_attempt()`）。
  目標フローは「達成ボタンが押されるまで `Attempt` は作られない」なので**ズレています**。
- **決定**：ヒント回数は用途が無くなった（AIは基本的に質問を返すし、復習問題の生成機能も廃止済み）ため、
  - `Attempt.hint_count` フィールドを削除（マイグレーション1本）
  - `Attempt` は**完了時にのみ**作成する（`completed_at` を入れて1件作る形でよい）
  - `action_type="HINT"` 自体を残すかはチャット機能側の判断。残す場合も `Attempt` は触らない
- **フロントへの影響**：`frontend/src/shared/types/index.ts` の `Attempt` 型に `hint_count` があるので、
  そちらの削除も必要です（共有ファイルのため、PR説明に他機能への影響を明記すること）。
- **解決済みか**：☐

### 2-5. 【決定D】`understood`（理解度の自己申告）の撤去

- **現状**：`send-message` の入力に `understood`（既定 `False`）があり、チャット側が
  `record_review_result(attempt, bool(understood))` として渡しています。
- **決定**：自己申告はしない。**復習側は既に `understood` を無視するようになりました**
  （固定評価で記録。`ReviewLog.performance_rating` フィールド自体は将来のために残置）。
- **やること**：チャット側から `understood` の入力項目と受け渡しを削除し、
  `record_review_result(attempt)` と呼ぶ。復習側の引数は互換のため残してあるので、
  削除後に `apps/reviews/services.py` の `understood` 引数も消してよいです。
- **注意**：以前は「理解できなかった」と申告すると復習間隔が1日に戻る仕様でしたが、
  この決定によりその挙動は無くなります（間隔は 1日→6日→係数倍 と伸びる一方）。
- **解決済みか**：☐

### 2-6. 【軽微】完了・ヒント時のユーザー発言が `CHANGE_METHOD` 種別で保存される

- **症状**：`action_type == "ANSWER"` 以外はすべて `CHANGE_METHOD`（解法変更ノード）扱いになるため、
  達成時に添えたコメントが思考グラフに「解法変更」として並びます。
- **直し方**：2-1 で完了を別エンドポイントに分ければ、この経路自体が無くなります。
- **解決済みか**：☐

### 2-7. `response_time_seconds` の計測方法

- **現状**：`attempt.completed_at - attempt.created_at` で算出しています。
  2-4 により `Attempt` を完了時のみ作るようになると、**この差はほぼ 0 になり無意味**です。
- **選択肢**：(a) 記録をやめる (b) セッション再開時刻から測る (c) その回の最初のメッセージから測る。
  現状 UI で使っていないので、(a) でも支障ありません。
- **解決済みか**：☐

### 2-8. 【CI】`ruff format` 未適用のチャット機能ファイル

- `develop` 時点で **CI が赤**です。フォーマット未適用が3ファイル残っています。

  ```
  backend/apps/chat/services.py
  backend/apps/chat/views.py
  backend/apps/chat/migrations/0004_merge_20260814_1404.py
  ```

  （`topics` 側の同種の指摘は本ブランチで解消済み）
- **直し方**：`cd backend && ruff format .`
- **解決済みか**：☐

### 2-9. `apps/chat/tests.py` が空

現在 `# Create your tests here.` の1行のみで、中心フローのテストがゼロです。
マージ後に最低限これらを追加してください（復習側の対応するテストは `apps/reviews/tests.py` にあります）。

- セッション作成直後は `Attempt` も `KnowledgeNode` も存在しないこと（パターン1-1）
- 本文なしで達成ボタンを押しても成功すること（2-1 の回帰防止）
- 達成時に `KnowledgeNode` と `Attempt` が**1件ずつ**できること（パターン1-3）
- 同じセッションで2回目の完了をすると `Attempt` が2件になること（パターン2-5）
- 他人の `node_id` ではセッションを作れないこと（2-2 の回帰防止）
- 完了処理の途中で例外が起きたとき、ノードもスケジュールも残らないこと（2-3 の回帰防止）

---

## 3. マージ後の再確認手順

ログイン済みのクライアントで以下を順に叩き、パターン1・2が通ることを確認します。

```
# パターン1
POST /api/chat-sessions/                      → 201。attempts=0, knowledge_node=null であること
POST /api/chat-sessions/{id}/send-message/    → 会話が成立すること
POST /api/topics/                             → 保存先トピックを作る
POST /api/chat-sessions/{id}/complete/        → 本文なしで 200。KnowledgeNode と Attempt が1件ずつ
    （2-1 を分離しない場合は send-message に COMPLETE で）

# パターン2
GET  /api/learning-tree/                      → 葉（knowledge_node）が木に出ること
GET  /api/review-schedules/                   → mastery_level / is_due / chat_session_id が返ること
GET  /api/review-schedules/due/               → 予定日を過ぎた葉だけが、古い順で返ること
POST /api/chat-sessions/  {"node_id": "..."}  → 同じセッションID が返る（入り直せる）
POST /api/chat-sessions/{id}/complete/        → Attempt が増え、次回予定日が伸びること
```

フロント側の木の色は、`/api/learning-tree/`（葉の一覧）と `/api/review-schedules/`（`mastery_level`・`is_due`）を
`node_id` で突き合わせて決めます。`/api/review-schedules/` に出てこない葉は
**ReviewSchedule がまだ無い＝未学習**なので、灰色で塗ってください。
木全体の定着率(%) は `is_due が false の葉 ÷ 木の葉の総数` です。
