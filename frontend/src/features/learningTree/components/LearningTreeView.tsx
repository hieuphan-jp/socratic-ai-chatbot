/**
 * features/learningTree/components/LearningTreeView.tsx
 *
 * JA: 学習内容を木構造で表示するメイン部品。GET /api/learning-tree/ (トピック階層+葉)と
 *     GET /api/review-schedules/ (葉ごとの定着度・復習タイミング)を node_id で
 *     突き合わせて色分けする(CONVENTIONS.md §12: 集計・色決定はフロントの責務)。
 *     検索欄はキーワードで葉を絞り込む(祖先トピックは残す)簡易フィルタ。
 * VI: Component chính hiển thị nội dung học dạng cây. Ghép GET /api/learning-tree/
 *     (phân cấp Topic + lá) với GET /api/review-schedules/ (độ ghi nhớ, thời điểm ôn
 *     của từng lá) theo node_id để tô màu (CONVENTIONS.md §12: tổng hợp/quyết định màu
 *     là việc của frontend). Ô tìm kiếm lọc lá theo từ khóa (giữ lại Topic tổ tiên).
 */
import { useMemo, useState } from 'react'

import { Search } from 'lucide-react'

import { useReviewSchedules } from '@/features/reviews/api/hooks'
import { useI18n } from '@/shared/i18n'
import { ErrorText } from '@/shared/ui'
import type { TreeNode } from '@/shared/types'

import { useLearningTree } from '../api/hooks'
import { computeRetentionPercent, indexSchedulesByNodeId } from '../lib/mastery'
import { NodeDetailPanel } from './NodeDetailPanel'
import { RetentionSummary } from './RetentionSummary'
import { TopicBranch } from './TopicBranch'

// JA: keyword を含む葉だけ残した木を作る(親は子が残る限り残す)。
// VI: Tạo lại cây chỉ giữ lá chứa keyword (node cha giữ lại nếu còn con).
function filterTree(nodes: TreeNode[], keyword: string): TreeNode[] {
  if (!keyword.trim()) return nodes
  const lower = keyword.toLowerCase()

  return nodes.flatMap((node) => {
    const children = node.children ? filterTree(node.children, keyword) : []
    const selfMatches = node.label.toLowerCase().includes(lower)
    if (selfMatches || children.length > 0) {
      return [{ ...node, children: children.length > 0 ? children : node.children }]
    }
    return []
  })
}

export function LearningTreeView() {
  const { t } = useI18n()
  const [keyword, setKeyword] = useState('')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const tree = useLearningTree()
  const schedules = useReviewSchedules()

  const scheduleByNodeId = useMemo(
    () => indexSchedulesByNodeId(schedules.data ?? []),
    [schedules.data]
  )
  const filtered = useMemo(
    () => (tree.data ? filterTree(tree.data, keyword) : []),
    [tree.data, keyword]
  )
  const retention = useMemo(
    () => computeRetentionPercent(tree.data ?? [], scheduleByNodeId),
    [tree.data, scheduleByNodeId]
  )

  if (tree.isPending) return <p className="text-sm text-slate-400">{t('common.loading')}</p>
  if (tree.isError) return <ErrorText>{(tree.error as Error).message}</ErrorText>

  return (
    <div className="space-y-4">
      <RetentionSummary
        percent={retention.percent}
        notDue={retention.notDue}
        total={retention.total}
      />

      <div className="relative">
        <Search className="pointer-events-none absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder={t('common.search')}
          className="w-full rounded-2xl border border-slate-200 bg-white py-2.5 pr-4 pl-10 text-sm outline-none transition-all focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
        />
      </div>

      {/* JA: ★lg:items-start が無いと、既定のgrid stretchで詳細パネルが左の木構造列と
              同じ高さに引き伸ばされる。葉が少なく木構造列が低いと、パネルのフッター
              (「復習を始める」ボタン)がパネルの見た目の外に押し出されて押せなくなる
              (NodeDetailPanel側のコメントも参照)。
              VI: ★Thiếu lg:items-start thì grid stretch mặc định sẽ kéo panel chi tiết
              cao bằng cột cây bên trái. Cây ít lá thì cột đó thấp, khiến footer của panel
              (nút "Bắt đầu ôn tập") bị đẩy ra ngoài khung nhìn, không bấm được (xem thêm
              comment ở NodeDetailPanel). */}
      <div
        className={`grid gap-4 ${selectedNodeId ? 'lg:grid-cols-[1fr_360px] lg:items-start' : 'grid-cols-1'}`}
      >
        <div className="space-y-1 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm">
          {filtered.length === 0 ? (
            <p className="px-2 py-6 text-center text-sm text-slate-400">{t('common.notFound')}</p>
          ) : (
            filtered.map((topic) => (
              <TopicBranch
                key={topic.id}
                topic={topic}
                scheduleByNodeId={scheduleByNodeId}
                selectedNodeId={selectedNodeId}
                onSelectNode={setSelectedNodeId}
                defaultOpen={keyword.trim().length > 0}
              />
            ))
          )}
        </div>

        {selectedNodeId && (
          <NodeDetailPanel
            nodeId={selectedNodeId}
            schedule={scheduleByNodeId.get(selectedNodeId)}
            onClose={() => setSelectedNodeId(null)}
          />
        )}
      </div>
    </div>
  )
}
