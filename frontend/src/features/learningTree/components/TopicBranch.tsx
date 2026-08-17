/**
 * features/learningTree/components/TopicBranch.tsx
 *
 * JA: 学習木の1トピック(棚)と、その直下の子トピック・葉(知識ノード)を再帰的に描画する。
 *     GET /api/learning-tree/ の children は「子トピック + 直属の知識ノード」を
 *     まとめて返すため(apps/topics/services.py の build_learning_tree)、
 *     type で分岐して描き分ける。
 *     ★2026-08 撤去: 以前は葉を選択すると、選択した葉への経路以外のTopic/葉を
 *     暗く縮小するフォーカスモードがあったが、他のノードが読みにくくなるという
 *     フィードバックにより廃止した(経路自動展開の計算ごと削除。lib/treeFocus.ts参照)。
 * VI: Vẽ đệ quy 1 Topic (kệ) và các Topic con / lá (knowledge node) trực thuộc.
 *     children của GET /api/learning-tree/ gộp chung "Topic con + knowledge node
 *     trực thuộc" (build_learning_tree ở apps/topics/services.py), nên tách theo
 *     type để vẽ khác nhau.
 *     ★Bỏ 08/2026: Trước đây khi chọn 1 lá, các Topic/lá không nằm trên đường dẫn
 *     tới lá đó sẽ bị làm mờ và thu nhỏ (chế độ focus), nhưng theo phản hồi là làm
 *     các node khác khó nhìn nên đã bỏ (xóa luôn phần tính đường dẫn tự mở, xem lib/treeFocus.ts).
 */
import { useState } from 'react'

import { ChevronRight, FolderTree } from 'lucide-react'

import type { ReviewSchedule, TreeNode } from '@/shared/types'

import { KnowledgeLeaf } from './KnowledgeLeaf'

interface TopicBranchProps {
  topic: TreeNode
  scheduleByNodeId: Map<string, ReviewSchedule>
  selectedNodeId: string | null
  onSelectNode: (nodeId: string) => void
  defaultOpen: boolean
  depth?: number
}

export function TopicBranch({
  topic,
  scheduleByNodeId,
  selectedNodeId,
  onSelectNode,
  defaultOpen,
  depth = 0,
}: TopicBranchProps) {
  const [open, setOpen] = useState(defaultOpen)
  const children = topic.children ?? []
  const childTopics = children.filter((c) => c.type === 'topic')
  const childNodes = children.filter((c) => c.type === 'knowledge_node')

  return (
    <div className={depth > 0 ? 'border-l border-slate-100 pl-4' : ''}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-xl border-0 bg-transparent px-2 py-1.5 text-left text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <ChevronRight
          className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform ${open ? 'rotate-90' : ''}`}
        />
        <FolderTree className="h-4 w-4 shrink-0 text-teal-600" />
        <span>{topic.label}</span>
      </button>

      {open && (
        <div className="mt-1 space-y-1 pl-2">
          {childNodes.map((node) => (
            <KnowledgeLeaf
              key={node.id}
              node={node}
              schedule={scheduleByNodeId.get(node.id)}
              isSelected={selectedNodeId === node.id}
              onSelect={onSelectNode}
            />
          ))}
          {childTopics.map((child) => (
            <TopicBranch
              key={child.id}
              topic={child}
              scheduleByNodeId={scheduleByNodeId}
              selectedNodeId={selectedNodeId}
              onSelectNode={onSelectNode}
              defaultOpen={defaultOpen}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
