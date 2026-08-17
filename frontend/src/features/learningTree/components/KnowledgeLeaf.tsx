/**
 * features/learningTree/components/KnowledgeLeaf.tsx
 *
 * JA: 学習木の葉(知識ノード)1件。緑の濃さ(mastery_level)と復習タイミング
 *     (is_due)は別軸で表現する(設計方針C)。
 * VI: Một lá (knowledge node) của cây học tập. Độ đậm xanh (mastery_level) và
 *     thời điểm ôn tập (is_due) hiển thị theo 2 trục riêng (phương án thiết kế C).
 */
import { BookOpen, Clock } from 'lucide-react'

import { useI18n } from '@/shared/i18n'
import type { ReviewSchedule, TreeNode } from '@/shared/types'
import { LeafButton } from '@/shared/ui/Leaf'

import { leafToneForMastery } from '../lib/mastery'

interface KnowledgeLeafProps {
  node: TreeNode
  schedule: ReviewSchedule | undefined
  isSelected: boolean
  onSelect: (nodeId: string) => void
  // JA: ★フォーカスモードで、選択されていない兄弟の葉を控えめにするためのフラグ。
  //     選択中の葉自身には付けない(常にisSelected側で強調する)。
  // VI: ★Cờ để làm mờ nhẹ lá anh em chưa được chọn trong chế độ focus.
  //     Không áp dụng cho chính lá đang chọn (luôn được nhấn mạnh qua isSelected).
  isDimmed?: boolean
}

export function KnowledgeLeaf({
  node,
  schedule,
  isSelected,
  onSelect,
  isDimmed = false,
}: KnowledgeLeafProps) {
  const { t } = useI18n()
  const masteryLevel = schedule?.mastery_level ?? 0
  const isDue = schedule?.is_due ?? false
  const tone = leafToneForMastery(masteryLevel)

  return (
    <LeafButton
      onClick={() => onSelect(node.id)}
      selected={isSelected}
      fill={tone.fill}
      stroke={tone.stroke}
      className={`group h-11 gap-2.5 text-sm transition-opacity duration-200 ${tone.textClassName} ${
        isDimmed ? 'opacity-45' : 'opacity-100'
      }`}
    >
      <BookOpen className="h-4 w-4 shrink-0 opacity-70" />
      <span className="min-w-0 flex-1 truncate font-medium">{node.label}</span>
      {isDue && (
        <span
          className="flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700"
          title={t('learningTree.review.dueTooltip')}
        >
          <Clock className="h-3 w-3" />
          {t('learningTree.review.badge')}
        </span>
      )}
    </LeafButton>
  )
}
