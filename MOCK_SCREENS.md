# モック画面ガイド：学習内容ツリー / ヒントチャット / Hướng dẫn màn hình mock: Cây học tập / Chat gợi ý

JA: ここでは「学習内容の検索木構造画面」と「ヒントチャット画面」の**モック実装**の使い方と、
実装を引き継ぐ担当者が今後やるべきことをまとめる。**バックエンドAPIはまだ無く**、フロントは
ダミーデータで動いている状態。実装時は必ず [`CONVENTIONS.md`](./CONVENTIONS.md) の§9パターンに従うこと。
VI: Tài liệu này tóm tắt cách dùng **bản mock** của "màn hình cây nội dung đã học (có tìm kiếm)" và
"màn hình chat gợi ý", cùng việc người phụ trách tiếp theo cần làm. **Chưa có backend API**, frontend
đang chạy bằng dữ liệu giả. Khi hiện thực thật, luôn theo pattern §9 của [`CONVENTIONS.md`](./CONVENTIONS.md).

---

## 1. 使い方 / Cách dùng

セットアップ・起動手順は [`README.md`](./README.md) の「セットアップ」章の通り（backend: `runserver`、frontend: `npm run dev`）。

1. `http://localhost:5173` を開き、デモユーザーでログイン。
2. ホーム画面のナビゲーションから以下のいずれかへ進む。
   - **学習内容ツリー** → `/learning-tree`
   - **ヒントチャット** → `/hint-chat`

JA: どちらも**未ログインだと表示できない**（`RequireAuth` で保護されたルート）。
VI: Cả hai đều **không xem được nếu chưa đăng nhập** (route được bảo vệ bởi `RequireAuth`).

### 1.1 学習内容ツリー画面 / Màn hình cây nội dung đã học（`/learning-tree`）
- 上部の検索ボックスにキーワードを入れると、該当ノードとその祖先だけが残るように木が絞り込まれる。
- ノードをクリックすると開閉する。
- 表示データは `frontend/src/features/learningTree/api/mockData.ts` の固定配列（数学/プログラミングの2カテゴリ）。

### 1.2 ヒントチャット画面 / Màn hình chat gợi ý（`/hint-chat`）
- 下部の入力欄に質問を入れて送信すると、ユーザー発言が右側に表示される。
- 約0.5秒後、`frontend/src/features/hintChat/api/mockData.ts` のキーワードマッチングで
  それらしいヒント文言が左側に返る（本物のAI応答ではない）。

---

## 2. 今のモックの限界 / Giới hạn của bản mock hiện tại

| 項目 / Mục | 現状 / Hiện trạng |
|---|---|
| データの永続化 / Lưu trữ | 無し。リロードで消える。 / Không có. Tải lại trang là mất. |
| バックエンドAPI / Backend API | 無し。`shared/api/client.ts` の `api` を一切使っていない。 / Không có. Chưa dùng `api` của `shared/api/client.ts`. |
| ヒントの中身 / Nội dung hint | キーワード一致による固定文言（`apps/ai` のLLM抽象化層は未接続）。 / Câu cố định theo từ khóa (chưa nối với tầng trừu tượng LLM ở `apps/ai`). |
| 学習内容ツリーの出所 / Nguồn cây nội dung | ハードコードされたJS配列。ユーザーごとの学習履歴は反映されない。 / Mảng JS hard-code, không phản ánh lịch sử học của từng user. |

---

## 3. 今後の実装タスク / Việc cần làm tiếp theo

### 3.1 学習内容ツリー機能 / Tính năng cây nội dung đã học

**Backend**（[`CONVENTIONS.md`](./CONVENTIONS.md) §4 の手順で新規app、§9.1 をコピー元に）
- [ ] 学習内容を表すモデル設計（例: カテゴリ／トピックの親子関係、`user` への紐付け、習熟度など）。木構造は `parent` 自己参照 FK か、固定階層のいずれかで検討。
- [ ] `get_queryset` で **必ず `request.user` に絞る**（§1 所有権の絞り込み）。
- [ ] 検索は DB 側（`icontains` 等）で行うか、件数次第でフロント側絞り込みのままにするかを設計時に決める。
- [ ] `services.py` に木構造の組み立てロジックを置く（`views.py` に業務ロジックを書かない）。

**Frontend**（[`CONVENTIONS.md`](./CONVENTIONS.md) §5 の手順、§9.2 をコピー元に）
- [ ] `shared/api/queryKeys.ts` に `learningTree` グループを追加。
- [ ] `shared/types/index.ts`（または feature 内）にバックエンドのシリアライザ出力と一致する `TreeNode` 型を定義し直す。
- [ ] `features/learningTree/api/hooks.ts` を新設し、`useQuery` + `api.get('/learning-tree/')` に置き換える。
- [ ] `features/learningTree/api/mockData.ts` は削除し、`LearningTreeView.tsx` の `fetchMockLearningTree()` 呼び出しを `useQuery` に差し替える。
- [ ] 読み込み中／エラー／空／データの4状態表示（§9.2 の `ItemList` 例を参考）。

### 3.2 ヒントチャット機能 / Tính năng chat gợi ý

**Backend**（新規app、§9.1 をコピー元に）
- [ ] チャットメッセージのモデル設計（`user`、`role`（user/hint）、`text`、会話セッション単位で分けるか等）。
- [ ] `services.py` でヒント生成ロジックを実装し、**`apps/ai` の `LLMProvider`（`chat()`）を呼び出す**。既定の `fake` 実装で開発し、`AI_PROVIDER=gemini` で切替可能にする（`gemini.py` は要実装、README参照）。
- [ ] `get_queryset` で `request.user` に絞る（他人の会話が見えないように）。
- [ ] 入力検証（空文字・長さ制限など）は `serializers.py` へ。

**Frontend**
- [ ] `shared/api/queryKeys.ts` に `hintChat` グループを追加。
- [ ] `features/hintChat/api/hooks.ts` を新設。送信は `useMutation` + `api.post('/hint-chat/messages/', { text })`、履歴取得は `useQuery` に置き換える。
- [ ] `features/hintChat/api/mockData.ts` は削除し、`HintChatView.tsx` の `setTimeout` によるモック応答・ローカル `useState` 管理をやめ、TanStack Query のキャッシュ（`onSuccess` で invalidate 等）に置き換える。
- [ ] 送信中・エラー時の表示を `useMutation` の `isPending` / `isError` から出す（現状の独自 `waiting` state を置き換える）。

---

## 4. このファイルの扱い / Về file này

JA: このファイルは両機能が本実装（バックエンドAPI接続）に移行したら役目を終える。実装が完了したら
本ファイルは削除し、必要な情報は各 feature 内のコメントや PR に引き継ぐこと。
VI: File này hết vai trò khi cả hai tính năng chuyển sang hiện thực thật (nối backend API). Khi hoàn tất,
xóa file này; thông tin cần thiết chuyển vào comment trong từng feature hoặc PR.
