/**
 * features/hintChat/components/StepLeafNode.tsx
 *
 * JA: 思考ツリーの1ステップを表す、平行四辺形の葉ノード(React Flowのカスタムノード)。
 *     木は下から上へ育つ(rankdir: 'BT')ため、ハンドルは target=下・source=上。
 *     幹(TRUNK)は葉色、分岐(BRANCH=古いステップへの枝分かれ)は少し違う色で
 *     「そこだけ新しい枝が生えた」ことが分かるようにする。
 * VI: Node lá hình bình hành cho 1 bước trong cây tư duy (custom node của React
 *     Flow). Cây mọc từ dưới lên (rankdir: 'BT') nên handle target=dưới,
 *     source=trên. Thân (TRUNK) dùng màu lá thường; rẽ nhánh (BRANCH = nhánh
 *     quay lại một bước cũ hơn) dùng màu hơi khác để thấy rõ "chỗ này vừa mọc
 *     nhánh mới".
 */
import { Handle, Position } from '@xyflow/react'

import { useI18n } from '@/shared/i18n'
import { Leaf } from '@/shared/ui/Leaf'
import type { StepKind } from '@/shared/types'

type StepLeafData = {
  step_label: string
  title: string
  text: string
  step_kind: StepKind
  parent_confirmed: boolean
}

export function StepLeafNode({ data }: { data: StepLeafData }) {
  const { t } = useI18n()
  const isBranch = data.step_kind === 'BRANCH'

  return (
    <div className="relative" style={{ width: 176, height: 60 }}>
      <Handle type="target" position={Position.Bottom} style={{ opacity: 0 }} />
      <Leaf
        fill={isBranch ? 'var(--color-amber-100)' : 'var(--color-leaf-100)'}
        stroke={isBranch ? 'var(--color-amber-400)' : 'var(--color-leaf-400)'}
        className="h-full w-full"
      >
        <span
          className={`text-[10px] font-semibold uppercase tracking-wide opacity-70 ${isBranch ? 'text-amber-800' : 'text-leaf-ink'}`}
        >
          STEP {data.step_label}
        </span>
        <span
          className={`line-clamp-2 text-center text-[11px] font-medium leading-tight ${isBranch ? 'text-amber-900' : 'text-leaf-ink'}`}
        >
          {data.title}
        </span>
      </Leaf>
      <Handle type="source" position={Position.Top} style={{ opacity: 0 }} />
      {!data.parent_confirmed && (
        <span
          className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-amber-500 ring-2 ring-white"
          title={t('hintChat.step.pendingParent')}
        />
      )}
    </div>
  )
}
