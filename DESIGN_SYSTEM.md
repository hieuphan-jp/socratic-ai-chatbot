# DESIGN_SYSTEM.md — デザイン規約 / Quy ước thiết kế

> JA: `CONVENTIONS.md` がコードの書き方の規約なのに対し、この文書は**見た目の規約**です。
> 誰がどの画面を触っても、出来上がりがバラバラにならないようにするための共通ルール。
> **迷ったら「自分で作らず、まず `shared/ui` を見る」**。
> VI: `CONVENTIONS.md` là quy ước cách viết code, còn tài liệu này là **quy ước về giao diện**.
> Luật chung để ai sửa màn hình nào thì kết quả vẫn đồng nhất.
> **Phân vân thì "đừng tự chế, hãy xem `shared/ui` trước"**.

> JA: 長い説明文は日本語のみ、**実際に参照するルール表は日本語＋ベトナム語**で書いています。
> VI: Phần diễn giải dài chỉ có tiếng Nhật; **các bảng luật hay tra cứu thì có cả tiếng Nhật và tiếng Việt**.

---

## 0. 前提と現在地 / Tiền đề và hiện trạng

このアプリは以前「インラインstyleの画面」と「Tailwindの画面」が混在していました。
今回、**全画面をTailwindに統一**し、**UI文言は3言語(日本語/ベトナム語/英語)切替**に移行します。

| 状態 / Trạng thái | 対象 / Đối tượng |
|---|---|
| ✅ 完了 / Xong | `shared/ui` 全部・`shared/i18n` 全部・`shared/lib/cn.ts`・`HomePage`・`LoginPage`・`features/auth`・`app/RequireAuth`・`app/providers` |
| 🔨 これから / Sắp làm | `features/learningTree`・`features/reviews`・`LearningTreePage`・`features/hintChat`・`HintChatPage`（残タスクは §5）|
| 🕓 全部終わってから / Sau khi xong hết | `index.css` の preflight 有効化（§7） |

**お手本にするファイル / File dùng làm mẫu:** `src/pages/HomePage.tsx`
新しく画面を作る・直すときは、まずこのファイルの形をコピーしてください。

---

## 1. デザインの考え方（トーン＆マナー）/ Tinh thần thiết kế

このアプリは「AIに問いかけられながら、自分で学ぶ」ためのものです。
UIは**主役ではなく、学習の邪魔をしない背景**であるべき、という前提で以下を決めています。

### 1-1. 4つの原則 / 4 nguyên tắc

| # | 原則 / Nguyên tắc | 具体的には / Cụ thể |
|---|---|---|
| 1 | **やわらかい** / Mềm mại | 角は大きめに丸める。彩度の低いパステルを使う。黒(#000)と原色は使わない。 / Bo góc lớn. Dùng pastel độ bão hòa thấp. Không dùng đen tuyền và màu nguyên. |
| 2 | **静か** / Tĩnh | 影は最小限(`shadow-sm`)。目立つ色は「今やること」だけに使う。 / Đổ bóng tối thiểu (`shadow-sm`). Màu nổi chỉ dành cho "việc cần làm ngay". |
| 3 | **一貫している** / Nhất quán | 同じ意味のものは同じ見た目。色・角丸・余白は §2 の表から選ぶだけにする。 / Cùng ý nghĩa thì cùng hình thức. Màu/bo góc/khoảng cách chỉ chọn từ bảng ở §2. |
| 4 | **急かさない** / Không hối thúc | アニメーションは状態変化を伝える最小限。点滅・カウントダウン・赤い警告を学習中に出さない。 / Animation chỉ đủ để báo đổi trạng thái. Không nhấp nháy, đếm ngược, cảnh báo đỏ khi đang học. |

### 1-2. やらないこと / Điều KHÔNG làm

- ダークモードは**対応しない**（明るい配色に絞る）/ **Không** làm dark mode.
- 新しいフォントをネットから読み込まない（表示のちらつきと遅延を避ける）/ Không tải web font qua mạng.
- 画面ごとの独自カラーを作らない（§2の役割表にない色を使わない）/ Không tự chế màu riêng cho từng màn hình.

---

## 2. トークン（色・文字・形）/ Token

### 2-1. 色の役割 / Vai trò của màu

**色は「何色にしたいか」ではなく「どういう意味か」で選びます。**
/ **Chọn màu theo Ý NGHĨA, không theo "muốn màu gì".**

| 役割 / Vai trò | 使う色 / Màu | 使う場所 / Dùng ở đâu |
|---|---|---|
| ブランド・主操作 / Thương hiệu, hành động chính | `teal-700`(hover `teal-800`) ※1 | 主ボタン、選択中のタブ、アイコン |
| 文字・枠・背景(中立) / Chữ, viền, nền (trung tính) | `slate-800/700/600/500/400` `slate-200/100` | 本文・見出し・枠線・補足 |
| 学びの定着 / Mức độ ghi nhớ | `leaf-50`〜`leaf-600`, `leaf-ink` | 学習木の葉、思考ツリーの葉 |
| 木の枝・幹 / Cành, thân cây | `branch-100/300/500/600` | 思考ツリーの線、根元の土 |
| 前向きな結果 / Kết quả tích cực | `emerald-*` | 定着率、完了メッセージ |
| 今やること / Việc cần làm ngay | `amber-*` | 復習期限、確認待ちバッジ |
| 失敗 / Lỗi | `rose-600` | エラー文、危険な操作 |
| リンク / Link | `indigo-600` | テキストリンク |

> `leaf-*` `branch-*` は Tailwind 標準にない独自トークンです。定義は `src/index.css` の `@theme`。

> ※1 2026-08 Figma側QAで検出: `teal-600` に白文字だとコントラスト比 3.66:1 で WCAG AA(通常文字4.5:1)未達。
> `teal-700` は 5.39:1 で合格するため全箇所差し替え済み(`Button.tsx` `SegmentedControl.tsx` `LearningTreePage.tsx`
> `ChatHistoryPanel.tsx` `ChatTimelineView.tsx` `NodeDetailPanel.tsx`)。新しく主色を使う時は必ず `teal-700` を使うこと。
> 色そのものを変えたい時は**この1箇所だけ**を直せば、2つの木の両方に反映されます。
> / `leaf-*` `branch-*` là token riêng (Tailwind không có sẵn), định nghĩa ở `@theme` trong `src/index.css`.
> Muốn đổi màu thì **chỉ sửa đúng chỗ đó**, cả hai cây đều tự đổi theo.

### 2-2. 文字 / Chữ

| 用途 / Dùng cho | クラス / Class |
|---|---|
| ページ見出し / Tiêu đề trang | `text-lg font-semibold text-slate-800` |
| セクション見出し / Tiêu đề mục | `text-sm font-semibold text-slate-800` |
| 本文 / Nội dung | `text-sm text-slate-600` |
| 補足・キャプション / Ghi chú | `text-xs text-slate-500` |
| バッジ / Badge | `text-[11px] font-medium` |
| 大きな数字 / Số lớn | `text-2xl font-semibold` |

フォントは `src/index.css` の `--font-sans` で全体に指定済み。OS標準の丸ゴシック系を優先します。
**画面側で `font-family` を指定しないでください。**
/ Font đã đặt toàn cục qua `--font-sans`. **Không chỉ định `font-family` ở phía màn hình.**

### 2-3. 形（角丸・余白・影）/ Hình (bo góc, khoảng cách, bóng)

| 要素 / Phần tử | 角丸 / Bo góc |
|---|---|
| ページ内の大きな面(Card) / Mặt lớn trong trang | `rounded-3xl` |
| ボタン・入力欄・内側の箱 / Nút, ô nhập, hộp bên trong | `rounded-2xl` |
| 小さな操作(タブの中身など) / Điều khiển nhỏ | `rounded-xl` |
| バッジ・ピル / Badge, pill | `rounded-full` |

- 余白は**必ず親側の `gap-*` で作る**。子要素に `margin` を付けない（相殺・二重指定の事故を防ぐ）。
  / Khoảng cách **luôn tạo bằng `gap-*` ở phần tử cha**. Không gắn `margin` lên con.
- 影は `shadow-sm` のみ。強調したい時は影ではなく**色**か**枠線**で表す。
  / Bóng chỉ dùng `shadow-sm`. Muốn nhấn mạnh thì dùng **màu** hoặc **viền**, không dùng bóng.

---

## 3. UIコンポーネントの指定 / Chỉ định component UI

**`@/shared/ui` から import します。個別ファイルを直接 import しないでください。**
/ **Import từ `@/shared/ui`. Không import thẳng từng file.**

```tsx
import { Button, Card, PageContainer, PageHeader } from '@/shared/ui'
```

| コンポーネント | いつ使うか / Dùng khi nào | 主なprops |
|---|---|---|
| `PageContainer` | 全ページの一番外側。必ず使う / Lớp ngoài cùng của mọi trang | `width`: `narrow`(入力系) / `normal`(既定) / `wide`(2カラム) |
| `PageHeader` | ページ先頭の見出し。必ず使う / Tiêu đề đầu trang | `title` `subtitle` `actions` |
| `Card` | 情報のまとまりを囲む面 / Mặt bao một khối thông tin | `tone`: `default` / `accent`(良い結果) / `attention`(要対応) / `muted`(補足) |
| `Button` | すべてのボタン / Mọi nút bấm | `variant`: `primary`(1画面1つ) / `secondary` / `ghost` / `danger`、`size`: `sm` / `md`、`block` |
| `Input` | 1行入力 / Ô nhập 1 dòng | `icon`(左に置くアイコン) |
| `Badge` | 状態を1語で示すピル / Pill trạng thái 1 từ | `tone`: `neutral` / `accent` / `attention` / `brand` |
| `SegmentedControl` | 2〜3個の排他切替 / Chuyển đổi loại trừ 2-3 mục | `options` `value` `onChange` `ariaLabel` |
| `Leaf` / `LeafButton` | 木の葉(平行四辺形) / Lá cây (hình bình hành) | `fill` `stroke` `selected` |
| `LoadingText` `ErrorText` `EmptyState` `Notice` | 読み込み中/エラー/空/補足の4状態 / 4 trạng thái | — |
| `LanguageSwitcher` | 言語切替。`PageHeader` の `actions` に置く / Đổi ngôn ngữ, đặt trong `actions` | — |

### 3-1. 一覧画面の4状態は必ず出し分ける / Màn danh sách BẮT BUỘC phân biệt 4 trạng thái

`CONVENTIONS.md` §9.2 の通り、データを取得する画面は必ずこの形にします。

```tsx
if (isPending) return <LoadingText>{t('common.loading')}</LoadingText>
if (isError)   return <ErrorText>{(error as Error).message}</ErrorText>
if (data.length === 0) return <EmptyState message={t('common.empty')} />
return <>{/* データ */}</>
```

### 3-2. 禁止事項 / Điều cấm

| ❌ やらない / Không làm | ✅ 代わりに / Thay bằng |
|---|---|
| `style={{ ... }}` を書く / Viết `style={{...}}` | Tailwind クラス。動的な値(幅%など)だけ例外 / Class Tailwind. Chỉ ngoại lệ với giá trị động (vd %) |
| `<button>` を裸で使う / Dùng `<button>` trần | `<Button>` を使う / Dùng `<Button>` |
| `Button` に `bg-*` や `rounded-*` を渡して上書き / Ghi đè `bg-*`, `rounded-*` lên `Button` | 新しい `variant` を `Button.tsx` に足す / Thêm `variant` mới vào `Button.tsx` |
| JSXに日本語を直書き / Viết thẳng tiếng Nhật vào JSX | `t('key')` を使う（§4）/ Dùng `t('key')` |
| 独自の hex 色 (`#2563eb` など) / Tự chế mã màu hex | §2-1 の役割表から選ぶ / Chọn từ bảng vai trò ở §2-1 |
| 新しい影・角丸の値を作る / Tự chế giá trị bóng, bo góc | §2-3 の表から選ぶ / Chọn từ bảng ở §2-3 |

> **preflight を切っているため**、`<button>` や `<input>` はブラウザ既定の枠線・背景が残ります。
> `shared/ui` の部品はこれを打ち消し済みなので、**必ず部品を経由してください**。
> / **Vì đang tắt preflight**, `<button>`/`<input>` vẫn còn viền/nền mặc định của trình duyệt.
> Component trong `shared/ui` đã khử sẵn, nên **luôn đi qua component**.

---

## 4. 多言語化のルール / Quy tắc đa ngôn ngữ

対応言語は **日本語 / Tiếng Việt / English** の3つ。選択は `localStorage` に保存（バックエンド不要）。

### 4-1. 使い方 / Cách dùng

```tsx
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()
<Button variant="primary">{t('learningTree.review.start')}</Button>
<span>{t('learningTree.due.overdue', { days: 3 })}</span>  {/* '{days}日超過' */}
```

### 4-2. 文言を追加する手順 / Các bước thêm câu chữ

1. その画面が属する名前空間のファイルを開く / Mở file namespace của màn hình đó
   - 学習木・復習 → `src/shared/i18n/messages/learningTree.ts`
   - チャット・思考ツリー → `src/shared/i18n/messages/hintChat.ts`
   - 認証・ホーム → `src/shared/i18n/messages/auth.ts`
   - **複数の画面で使い回すものだけ** → `common.ts`
     （ここは全画面に影響するので、1画面のためだけのキーは入れない）
     / **Chỉ cái nào dùng lại ở nhiều màn hình** mới cho vào `common.ts`
     (chỗ này ảnh hưởng mọi màn hình, đừng bỏ khóa chỉ dùng cho 1 màn vào đây)
2. `ja` にキーと日本語を追加 / Thêm khóa + tiếng Nhật vào `ja`
3. `vi` と `en` にも同じキーを追加 / Thêm cùng khóa vào `vi` và `en`
4. `npm run typecheck` で確認 / Chạy `npm run typecheck`

> **1言語でも書き忘れると型エラーになります**（CIで止まる）。これが翻訳漏れ防止の仕組みです。
> / **Quên một ngôn ngữ là báo lỗi kiểu ngay** (CI sẽ chặn). Đây chính là cơ chế chống sót bản dịch.

### 4-3. キーの命名 / Đặt tên khóa

`名前空間.画面や部品.用途` の形。必ず自分の名前空間で始めること。
/ Dạng `namespace.màn-hình-hoặc-component.mục-đích`. Luôn bắt đầu bằng namespace của mình.

```
learningTree.review.start     ✅
hintChat.tree.title           ✅
common.loading                ✅（共通のものだけ）
startButton                   ❌ 名前空間が無い / Thiếu namespace
```

### 4-4. 注意 / Lưu ý

- **コード内のコメントは今まで通り日本語＋ベトナム語**（`CONVENTIONS.md` §6）。これは開発者向けなので i18n の対象外です。
  / **Comment trong code vẫn giữ tiếng Nhật + tiếng Việt** (§6). Đây là cho lập trình viên, không thuộc phạm vi i18n.
- サーバーから来るエラーメッセージは今のところ翻訳できません（バックエンドが日本語＋ベトナム語の固定文を返すため）。§8 の課題として残しています。
  / Thông báo lỗi từ server hiện chưa dịch được (backend trả chuỗi cố định Nhật+Việt). Ghi lại ở §8.

---

## 5. 残タスク一覧 / Danh sách việc còn lại

**デザイン実装は一人で進めます**（当初は二人で分担する想定でしたが方針変更）。
下は残っている画面の作業一覧です。**上から順にやる必要はありません**が、
feature 単位でまとめてやると `npm run build` の確認が1回で済みます。
/ **Phần triển khai giao diện do một người làm** (ban đầu định chia hai người, sau đã đổi).
Dưới là danh sách màn hình còn lại. **Không bắt buộc làm theo thứ tự**, nhưng gom theo
từng feature thì chỉ cần kiểm tra `npm run build` một lần.

### 5-1. 学習木・復習まわり / Cây học tập & ôn tập

- [ ] `pages/LearningTreePage.tsx` — `PageContainer`+`PageHeader`+`SegmentedControl` に置換、文言を `t()` 化
- [ ] `features/learningTree/components/LearningTreeView.tsx` — 検索欄を `Input icon={<Search/>}` に、4状態を §3-1 の形に
- [ ] `features/learningTree/components/TopicBranch.tsx` — `<button>` → `<Button variant="ghost">`
- [ ] `features/learningTree/components/KnowledgeLeaf.tsx` — 文言の `t()` 化（葉の形は変更不要）
- [ ] `features/learningTree/components/NodeDetailPanel.tsx` — タブを `SegmentedControl` に、ボタンを `Button variant="primary" block` に
- [ ] `features/learningTree/components/RetentionSummary.tsx` — `Card tone="accent"` に置換
- [ ] `features/learningTree/components/ChatHistoryPanel.tsx` `ChatTimelineView.tsx` — 文言の `t()` 化、`Card`/`Badge` に置換
- [ ] `features/reviews/components/DueReviewList.tsx` — `Card tone="attention"`+`Badge tone="attention"` に置換
- [ ] `shared/i18n/messages/learningTree.ts` — 上記で使う文言を3言語で追加

### 5-2. チャット・思考ツリーまわり / Chat & cây tư duy

> ⚠️ この feature は**枝分かれ判定ロジックが別途進行中**の場合があります。
> 着手前に、そちらの作業が終わっているか（またはブランチが分かれているか）を確認してください。
> / ⚠️ Feature này có thể **đang được sửa song song phần logic phán đoán rẽ nhánh**.
> Trước khi bắt tay, hãy kiểm tra việc đó đã xong chưa (hoặc đã tách nhánh chưa).

- [ ] `pages/HintChatPage.tsx` — `PageContainer width="wide"`+`PageHeader` に置換
- [ ] `features/hintChat/components/HintChatView.tsx` — **最大の作業**。29箇所のインラインstyleをTailwind化、文言を `t()` 化
- [ ] `features/hintChat/components/TopicFolderPicker.tsx` — インラインstyleをTailwind化、`Button`/`Input`/`Card` に置換
- [ ] `features/hintChat/components/TreeOverview.tsx` — Tailwind化
- [ ] `features/hintChat/components/StepLeafNode.tsx` — 文言の `t()` 化（葉の形は変更不要）
- [ ] `shared/i18n/messages/hintChat.ts` — 上記で使う文言を3言語で追加

### 5-3. 変更に注意が必要なファイル / File cần thận trọng khi sửa

`shared/ui/*`・`shared/i18n/index.tsx`・`shared/i18n/locale.ts`・`shared/lib/cn.ts`・`index.css` の `@theme`

これらは**全画面に影響する共通土台**です。1画面のために直すと他が壊れます。
「この画面だけ見た目を変えたい」で触らないこと。新しい見た目が必要なら、
`Button` の `variant` を増やすなど**選択肢を足す**形で対応してください。
/ Đây là **nền chung ảnh hưởng tới mọi màn hình**. Sửa vì 1 màn hình sẽ làm vỡ màn khác.
Đừng đụng vào chỉ vì "muốn đổi riêng màn này". Cần hình thức mới thì **thêm lựa chọn**
(vd thêm `variant` cho `Button`).

> 特に `index.css` の `@theme` は **Figma Variables と名前を一致させている**ため
> （§9 参照）、片方だけ変えると往復のたびにズレます。
> / Đặc biệt `@theme` trong `index.css` **được đặt tên khớp với Figma Variables** (xem §9),
> nên đổi một bên thôi là mỗi lần đồng bộ lại lệch.

---

## 6. PR前チェックリスト / Checklist trước khi PR

- [ ] `style={{...}}` が残っていないか（動的な値の例外を除く）/ Còn sót `style={{...}}` không
- [ ] 裸の `<button>` `<input>` が残っていないか / Còn `<button>`/`<input>` trần không
- [ ] JSXに日本語が直書きされていないか / Còn viết thẳng tiếng Nhật trong JSX không
- [ ] `ja` `vi` `en` の3言語すべてに文言を書いたか / Đã viết đủ 3 ngôn ngữ chưa
- [ ] 3言語すべてに切り替えて表示崩れが無いか（特にベトナム語は文字数が増えやすい）/ Đã đổi thử cả 3 ngôn ngữ xem có vỡ layout không (tiếng Việt hay dài hơn)
- [ ] 一覧画面で4状態(読込中/エラー/空/データ)を出し分けたか / Đã phân biệt đủ 4 trạng thái chưa
- [ ] `npm run typecheck && npm run build` が通るか / `npm run typecheck && npm run build` có pass không

---

## 7. 全画面が終わってからやること / Việc làm sau khi xong hết màn hình

§5 の残タスクが**全部**終わってから、以下を行います。

1. `src/index.css` の preflight を有効化する
   ```css
   @import 'tailwindcss/preflight.css' layer(base);  /* ← この行を追加 */
   ```
2. 全画面を目視で確認する（3言語 × 全画面）

> preflight はブラウザ既定のスタイルを全消しするものです。インラインstyleの画面が
> 1つでも残っている状態で有効にすると、そこが崩れます。**必ず §5 が全部終わってから**。
> / preflight xóa sạch style mặc định của trình duyệt. Nếu còn dù chỉ 1 màn hình dùng inline style
> mà bật lên là màn đó sẽ vỡ. **Bắt buộc làm sau khi §5 xong hết.**

有効化後は、`shared/ui` の各部品に入れてある `border-0` `bg-transparent` などの打ち消し指定が
不要になります（消してもよいし、残しても害はありません）。

---

## 8. 未対応・今後の課題 / Chưa làm & việc sau này

| 項目 / Mục | 状況 / Tình trạng |
|---|---|
| サーバー由来のエラーメッセージの翻訳 / Dịch thông báo lỗi từ server | バックエンドが日本語＋ベトナム語の固定文字列を返している。3言語対応するならエラーコードを返す設計に変える必要あり |
| 複数形・日付書式の言語別対応 / Số nhiều, định dạng ngày theo ngôn ngữ | 自前実装のため未対応。必要になったら `Intl.DateTimeFormat` を `shared/i18n` に足す |
| レスポンシブ(スマホ幅) / Responsive (khổ điện thoại) | `sm:` の指定は入れてあるが、実機での確認は未実施 |
| ダークモード / Dark mode | 対応しない方針（§1-2）|

---

## 9. Figma との往復 / Đồng bộ hai chiều với Figma

> **状態: 構築中（トークンと Foundations は完成、コンポーネントは作成中）**
> / **Trạng thái: đang dựng (token và Foundations đã xong, component đang làm)**
>
> **ファイル / File:** https://www.figma.com/design/GcbvzgJkInPUs782SAjW6J
> （`chill_education Design System`）

Figma の公式 MCP サーバー経由で、コード ⇄ Figma を双方向に編集できるようにします。
/ Chỉnh sửa hai chiều code ⇄ Figma qua MCP server chính thức của Figma.

### 9-0. Figma 側のフォントについて / Về font ở phía Figma

Figma ファイルは **Noto Sans JP** を使っています。コードの `--font-sans`（OS依存の丸ゴシック）
とは**意図的に違います**。理由:

- 丸ゴシックの `Zen Maru Gothic` は **ベトナム語の声調記号（ề ế ầ）が崩れる**ことを実測で確認したため。
  3言語すべてを Figma 上で検証できること（§6 のチェックリスト）を優先しました。
- `Hiragino Maru Gothic ProN`（コードの第一候補）は Figma で使えません（OSローカルフォントのため）。
- SemiBold(600) が無いため、Figma 上では `font-semibold` → **Bold**、`font-medium` → **Medium** で代替。

/ File Figma dùng **Noto Sans JP**, **cố ý khác** với `--font-sans` của code (font tròn theo OS). Lý do:
`Zen Maru Gothic` (font tròn) **vỡ dấu thanh tiếng Việt (ề ế ầ)** — đã kiểm chứng thực tế; ưu tiên việc
kiểm tra được cả 3 ngôn ngữ ngay trên Figma. `Hiragino Maru Gothic ProN` không dùng được trên Figma.
Không có SemiBold(600) nên trên Figma thay `font-semibold` → **Bold**, `font-medium` → **Medium**.

**実アプリの見た目は変わりません**（コードは `--font-sans` のまま）。この差はFigmaファイル内だけの話です。
/ **Giao diện app thật không đổi** (code vẫn dùng `--font-sans`). Khác biệt này chỉ nằm trong file Figma.

### 9-1. 唯一かつ最重要のルール / Quy tắc quan trọng nhất

**Figma Variables の名前を、`index.css` の `@theme` トークン名と完全に一致させること。**
/ **Tên Figma Variables phải TRÙNG KHỚP với tên token `@theme` trong `index.css`.**

| コード / Code | Figma Variable |
|---|---|
| `--color-leaf-400` | `leaf/400`（Primitives）|
| `--color-branch-500` | `branch/500`（Primitives）|
| `bg-teal-700`（主操作、※1参照）/ (hành động chính) | `brand/primary`（Semantic）|
| `mastery.ts` の `LEAF_TONES[3]` | `mastery/3/fill` + `mastery/3/stroke` |
| `StepLeafNode.tsx` の分岐色 | `step/branch/fill` + `step/branch/stroke` |
| `rounded-2xl` | `radius/2xl` |
| `gap-4`（16px）| `spacing/xl` ※ |

※ Figma の変数名に**ドットが使えない**ため、Tailwind の段階名（`0.5` `1.5` `2.5`）はそのまま使えません。
t-shirt 名（`3xs`〜`3xl`）にし、対応する Tailwind クラスを各変数の説明に書いてあります。
/ ※ Tên biến Figma **không cho phép dấu chấm**, nên không dùng được tên bậc của Tailwind (`0.5`, `1.5`...).
Đã đổi sang tên t-shirt (`3xs`–`3xl`), phần Tailwind tương ứng ghi trong description của từng biến.

**Primitives は `scopes: []`** にしてあり、デザイン時のカラーピッカーに出ません。
これにより `leaf/400` を直接塗ることができず、必ず `mastery/3/fill` のような**役割経由**になります。
/ **Primitives để `scopes: []`** nên không xuất hiện trong bảng chọn màu — buộc phải đi qua vai trò.

これを守らないと、Figma から戻ってくるコードが `bg-[#8cbd78]` のような**生の16進値**になり、
§2-1 で決めた「色は役割で選ぶ」「変えたい時は1箇所だけ直す」というルールが往復1回で壊れます。
/ Không giữ đúng thì code lấy về từ Figma sẽ là **mã hex thô** như `bg-[#8cbd78]`, và quy tắc
"chọn màu theo vai trò", "muốn đổi chỉ sửa 1 chỗ" ở §2-1 sẽ vỡ ngay sau 1 lần đồng bộ.

### 9-2. 構築の順番 / Thứ tự dựng

**必ずこの順で行います**（画面を先に作ると、変数が紐づかず作り直しになります）。
/ **Bắt buộc theo thứ tự này** (làm màn hình trước thì biến không gắn được, phải làm lại).

1. Figma ファイルを新規作成 / Tạo file Figma mới
2. `index.css @theme` + §2 → **Figma Variables**（色・文字・角丸）
3. `shared/ui/*` → **Figma コンポーネント**（`variant` 付き）
4. 画面（`HomePage` など）を 3 の部品で組み立てる / Dựng màn hình bằng component ở bước 3

### 9-3. 注意 / Lưu ý

- **読み取り系ツールには回数制限があります**（Full 座席で 1日200回 / 1分10回程度）。
  「全画面まとめて読ませる」はすぐ制限に達します。**フレームを選択して必要な分だけ**。
  / **Tool đọc có giới hạn số lần** (~200 lần/ngày, 10 lần/phút với ghế Full).
  Đừng đọc cả loạt màn hình; **chọn frame và chỉ đọc phần cần**.
- 書き込み系（`generate_figma_design` など）は制限対象外。
  / Tool ghi (`generate_figma_design`...) không bị giới hạn.
- Figma で新しい色や部品を足したら、**コード側の `@theme` / `shared/ui` にも必ず反映**する。
  片方だけ増えると往復のたびに差分が出ます。
  / Thêm màu/component mới ở Figma thì **phải phản ánh cả vào `@theme` / `shared/ui`** phía code.
  Chỉ thêm một bên là mỗi lần đồng bộ lại sinh khác biệt.
