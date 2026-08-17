/**
 * features/learningTree/components/KnowledgeLeaf.tsx
 *
 * JA: 学習木の葉(知識ノード)1件。緑の濃さ(mastery_level)と復習タイミング
 *     (is_due)は別軸で表現する(設計方針C)。
 *     ★2026-08 一時対応: 平行四辺形(shared/ui/Leaf の LeafButton)は斜辺が%指定・
 *     中身のpaddingがpx固定のため、葉が細いとタイトルが斜辺からはみ出す不具合が
 *     あった。斜辺と中身の safe area を正しく連動させる作り直しは後回しにし、
 *     まずは崩れない角丸長方形に戻して安全を優先する。色(mastery)とdueバッジは
 *     そのまま維持。チャット側の思考ツリー(StepLeafNode)や shared/ui/Leaf 自体は
 *     対象外(不具合が出ているのは学習木の知識ノードのみのため)。
 * VI: Một lá (knowledge node) của cây học tập. Độ đậm xanh (mastery_level) và
 *     thời điểm ôn tập (is_due) hiển thị theo 2 trục riêng (phương án thiết kế C).
 *     ★Tạm xử lý 08/2026: hình bình hành (LeafButton của shared/ui/Leaf) có cạnh
 *     xiên tính theo %, còn padding nội dung lại cố định theo px, nên lá hẹp bị
 *     tiêu đề tràn ra ngoài cạnh xiên. Việc làm lại cho đúng safe area để sau; giờ
 *     ưu tiên an toàn bằng hình chữ nhật bo góc không bị vỡ. Giữ nguyên màu theo
 *     mastery và badge due. Không đụng tới cây tư duy chat (StepLeafNode) hay
 *     shared/ui/Leaf (lỗi chỉ xảy ra ở knowledge node của cây học tập).
 */
import { BookOpen, Clock } from 'lucide-react'

import { useI18n } from '@/shared/i18n'
import type { ReviewSchedule, TreeNode } from '@/shared/types'

import { leafToneForMastery } from '../lib/mastery'

interface KnowledgeLeafProps {
  node: TreeNode
  schedule: ReviewSchedule | undefined
  isSelected: boolean
  onSelect: (nodeId: string) => void
}

export function KnowledgeLeaf({ node, schedule, isSelected, onSelect }: KnowledgeLeafProps) {
  const { t } = useI18n()
  const masteryLevel = schedule?.mastery_level ?? 0
  const isDue = schedule?.is_due ?? false
  const tone = leafToneForMastery(masteryLevel)

  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      style={{ backgroundColor: tone.fill, borderColor: tone.stroke }}
      className={`flex h-11 w-full items-center gap-2.5 rounded-2xl border-2 px-4 text-left text-sm ${
        tone.textClassName
      } ${isSelected ? 'ring-2 ring-indigo-400' : ''}`}
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
    </button>
  )
}
