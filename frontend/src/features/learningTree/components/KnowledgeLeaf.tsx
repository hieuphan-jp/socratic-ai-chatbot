/**
 * features/learningTree/components/KnowledgeLeaf.tsx
 *
 * JA: 学習木の葉(知識ノード)1件。緑の濃さ(mastery_level)と復習タイミング
 *     (is_due)は別軸で表現する(設計方針C)。
 * VI: Một lá (knowledge node) của cây học tập. Độ đậm xanh (mastery_level) và
 *     thời điểm ôn tập (is_due) hiển thị theo 2 trục riêng (phương án thiết kế C).
 */
import { BookOpen, Clock } from 'lucide-react'

import type { ReviewSchedule, TreeNode } from '@/shared/types'

import { leafStyleForMastery } from '../lib/mastery'

interface KnowledgeLeafProps {
  node: TreeNode
  schedule: ReviewSchedule | undefined
  isSelected: boolean
  onSelect: (nodeId: string) => void
}

export function KnowledgeLeaf({ node, schedule, isSelected, onSelect }: KnowledgeLeafProps) {
  const masteryLevel = schedule?.mastery_level ?? 0
  const isDue = schedule?.is_due ?? false

  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      className={`group flex w-full items-center gap-2.5 rounded-2xl border px-3 py-2 text-left text-sm transition-all ${leafStyleForMastery(
        masteryLevel
      )} ${isSelected ? 'ring-2 ring-indigo-400 ring-offset-1' : 'hover:shadow-sm'}`}
    >
      <BookOpen className="h-4 w-4 shrink-0 opacity-70" />
      <span className="min-w-0 flex-1 truncate font-medium">{node.label}</span>
      {isDue && (
        <span
          className="flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700"
          title="復習の時期です / Đã tới lúc ôn tập"
        >
          <Clock className="h-3 w-3" />
          復習
        </span>
      )}
    </button>
  )
}
