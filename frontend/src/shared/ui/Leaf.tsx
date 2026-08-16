/**
 * shared/ui/Leaf.tsx
 *
 * JA: 「木」UI(学習木・チャットの思考ツリー)で共通して使う、平行四辺形の葉の
 *     形そのものだけを担当する部品。色・中身はfeature側が決める(このファイルは
 *     形とレイアウトの器のみを持ち、業務ロジックや配色ルールを持ち込まない)。
 *     ★形はSVGのpolygonで描く(CSSのclip-pathだと斜辺には枠線が引けず、
 *       隣り合う葉同士が線無しでくっついて見えてしまうため)。
 * VI: Bộ phận chỉ đảm nhiệm HÌNH DẠNG lá hình bình hành, dùng chung cho 2 UI
 *     "cây" (cây học tập, cây tư duy của chat). Màu sắc/nội dung do phía feature
 *     quyết định (file này chỉ giữ hình dạng + layout, không mang logic nghiệp vụ
 *     hay quy tắc phối màu).
 *     ★Vẽ hình bằng polygon của SVG (vì clip-path CSS không vẽ được viền ở cạnh
 *       xiên, khiến các lá liền kề dính vào nhau không có đường phân tách).
 */
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react'

// JA: 平行四辺形の頂点(viewBox 0 0 100 100)。左上を右へ、右下を左へずらして
//     斜辺を作る。2,98側に少し余白を取り、strokeが上下端で欠けないようにする。
// VI: Đỉnh của hình bình hành (viewBox 0 0 100 100). Dịch góc trên-trái sang phải,
//     góc dưới-phải sang trái để tạo cạnh xiên. Chừa lề nhỏ ở 2,98 để viền không
//     bị cắt mất ở mép trên/dưới.
const LEAF_POINTS = '14,3 98,3 86,97 2,97'

function LeafShape({ fill, stroke }: { fill: string; stroke: string }) {
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polygon points={LEAF_POINTS} fill={fill} />
      <polygon
        points={LEAF_POINTS}
        fill="none"
        stroke={stroke}
        strokeWidth={3}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

type LeafToneProps = {
  /** JA: 塗り色(CSS color値。例: '#e2eeda') VI: Màu nền (giá trị màu CSS, vd '#e2eeda') */
  fill: string
  /** JA: 枠線色 VI: Màu viền */
  stroke: string
}

type LeafProps = HTMLAttributes<HTMLDivElement> & LeafToneProps & { selected?: boolean }

export function Leaf({ selected, fill, stroke, className = '', children, ...rest }: LeafProps) {
  return (
    <div
      {...rest}
      className={`relative flex items-center justify-center ${
        selected ? 'drop-shadow-[0_0_0_2px_theme(colors.indigo.400)]' : ''
      } ${className}`}
    >
      <LeafShape fill={fill} stroke={stroke} />
      <div className="relative flex flex-col items-center px-5">{children}</div>
    </div>
  )
}

type LeafButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  LeafToneProps & { selected?: boolean; children: ReactNode }

// JA: クリック操作が要る場所(学習木の葉など)用。見た目はLeafと同じ。
// VI: Dùng cho chỗ cần bấm được (lá của cây học tập, v.v). Hình thức giống hệt Leaf.
export function LeafButton({
  selected,
  fill,
  stroke,
  className = '',
  children,
  ...rest
}: LeafButtonProps) {
  return (
    <button
      {...rest}
      type="button"
      className={`relative flex w-full items-center border-0 bg-transparent text-left transition-transform hover:scale-[1.01] ${
        selected ? 'drop-shadow-[0_0_0_2px_theme(colors.indigo.400)]' : ''
      } ${className}`}
    >
      <LeafShape fill={fill} stroke={stroke} />
      <div className="relative flex w-full items-center px-5">{children}</div>
    </button>
  )
}
