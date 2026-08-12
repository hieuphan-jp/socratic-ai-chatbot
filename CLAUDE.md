# CLAUDE.md

このリポジトリで作業する際は、まず `CONVENTIONS.md` を読んで開発規約を把握すること。

## コードレビュー時の必須チェック項目

`/code-review` スキルが発火したとき（`/code-review <ブランチ名>` / `/code-review <PR番号>` / `/code-review ultra` を含む、対象がこのリポジトリのブランチ・PRである場合すべて）は、通常の観点（correctness / simplification / efficiency）に加えて、**以下の3点を必ず確認し、該当する逸脱があれば findings として報告する**こと。

1. **レイヤー依存の逸脱がないか**
   `CONVENTIONS.md` §1・§9 のパターン（`views → services → models` の一方向依存）から外れていないか。特に:
   - `services.py` が `views`/`request`/HTTP関連のものを import していないか
   - 業務ロジックが `views.py` に直接書かれていないか
   - 一覧・詳細系のエンドポイントで `get_queryset` が `request.user` に絞り込まれているか（§1 所有権の絞り込み）

2. **共有ファイルへの変更が他機能を壊していないか**
   `frontend/src/shared/types/index.ts` や `frontend/src/shared/api/queryKeys.ts` など、複数の feature が共有するファイルに変更が入っている場合:
   - 既存の型・クエリキーを変更/削除していないか（他featureが参照している可能性がある）
   - 追加が既存のキー構造・命名パターンと一貫しているか
   - 変更が今回のPRの対象feature以外に影響しうる場合、PR説明にその影響が明記されているか（§7 の「他メンバーへの影響」記載ルール）

3. **他アプリが所有するモデルへの直接アクセスがないか**
   `KNOWLEDGE_NODE` など、他の機能（Django アプリ）が所有するモデルに対して:
   - 所有アプリ以外から直接 ORM クエリ（`Model.objects.filter(...)` 等）でアクセスしていないか
   - 所有アプリの `services.py` の関数経由でアクセスしているか
   - 新しい FK 参照を追加している場合、依存の向きが一方向になっているか（循環依存がないか）

上記3点は、通常のコードレビューでは見落とされやすい「複数チーム間の設計整合性」に関わる観点なので、diff 上で該当箇所が見当たらない場合でも、変更されたファイルの一覧から該当領域（`shared/`、他アプリのモデル）に触れているかどうかを必ず確認すること。
