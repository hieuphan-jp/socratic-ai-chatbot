/**
 * shared/ui/index.tsx
 *
 * JA: 共通UI部品の窓口。画面側は必ず `@/shared/ui` からまとめて import する
 *     (個別ファイルを直接 import しない = 置き場所を変えても画面を壊さないため)。
 *
 *     ★2026-08 デザイン統一: ここにあった Button/Input/Notice/ErrorText の
 *     インラインstyle実装をやめ、Tailwind版に置き換えた。import 名は同じなので
 *     既存画面はそのまま動くが、見た目は新しいトークン(角丸2xl・teal基調)に揃う。
 *
 *     どの部品をいつ使うかは DESIGN_SYSTEM.md を参照。ここに無い見た目が必要に
 *     なったら、画面側で作り込む前にまずこのフォルダに足すか相談すること。
 * VI: Cửa vào của bộ UI dùng chung. Phía màn hình LUÔN import gộp từ `@/shared/ui`
 *     (không import thẳng từng file = đổi chỗ đặt file cũng không vỡ màn hình).
 *
 *     ★Thống nhất thiết kế 2026-08: đã bỏ bản inline style của Button/Input/Notice/
 *     ErrorText ở đây, thay bằng bản Tailwind. Tên import giữ nguyên nên màn hình cũ
 *     vẫn chạy, nhưng giao diện sẽ khớp token mới (bo góc 2xl, tông teal).
 *
 *     Dùng component nào lúc nào: xem DESIGN_SYSTEM.md. Cần một hình thức chưa có ở
 *     đây thì trước khi tự chế trong màn hình, hãy thêm vào thư mục này hoặc trao đổi trước.
 */
export { Badge } from './Badge'
export type { BadgeTone } from './Badge'

export { Button } from './Button'
export type { ButtonSize, ButtonVariant } from './Button'

export { Card } from './Card'
export type { CardTone } from './Card'

export { EmptyState, ErrorText, LoadingText, Notice } from './Feedback'

export { Input } from './Input'

export { LanguageSwitcher } from './LanguageSwitcher'

export { Leaf, LeafButton } from './Leaf'

export { PageContainer } from './PageContainer'

export { PageHeader } from './PageHeader'

export { SegmentedControl } from './SegmentedControl'
export type { SegmentedOption } from './SegmentedControl'
