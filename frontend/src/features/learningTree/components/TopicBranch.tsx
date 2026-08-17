/**
 * features/learningTree/components/TopicBranch.tsx
 *
 * JA: 学習木の1トピック(棚)と、その直下の子トピック・葉(知識ノード)を再帰的に描画する。
 *     GET /api/learning-tree/ の children は「子トピック + 直属の知識ノード」を
 *     まとめて返すため(apps/topics/services.py の build_learning_tree)、
 *     type で分岐して描き分ける。
 *     ★フォーカスモード: focusedTopicIds が渡されている(=葉が選択されている)間は、
 *     選択した葉への経路上にあるTopicだけを開いたまま見せ、それ以外は暗く縮小して
 *     折りたたむ。ノード数が増えても「今どこを見ているか」が迷子にならないようにする
 *     ための仕掛け。ユーザーが手動で開いたTopicは、経路から外れても展開状態
 *     (openのstate)自体は保持するので、フォーカス解除後は元の開閉状態に戻る。
 * VI: Vẽ đệ quy 1 Topic (kệ) và các Topic con / lá (knowledge node) trực thuộc.
 *     children của GET /api/learning-tree/ gộp chung "Topic con + knowledge node
 *     trực thuộc" (build_learning_tree ở apps/topics/services.py), nên tách theo
 *     type để vẽ khác nhau.
 *     ★Chế độ focus: khi có focusedTopicIds (nghĩa là đang chọn 1 lá), chỉ các Topic
 *     nằm trên đường dẫn tới lá đó được giữ mở, phần còn lại làm mờ và thu gọn lại.
 *     Mục đích để không bị lạc "đang xem chỗ nào" khi số node tăng lên. Topic nào
 *     user tự mở tay thì vẫn giữ nguyên state open dù rời khỏi đường dẫn, nên khi tắt
 *     chế độ focus sẽ trở lại đúng trạng thái đóng/mở trước đó.
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
  // JA: nullならフォーカス無効(従来通り)。Setがあれば、そこに含まれるTopic idだけが
  //     選択中の葉への経路(自分自身を含む)。 VI: null thì tắt focus (như cũ). Có Set thì
  //     chỉ những Topic id trong đó nằm trên đường dẫn tới lá đang chọn (gồm cả chính nó).
  focusedTopicIds?: Set<string> | null
}

export function TopicBranch({
  topic,
  scheduleByNodeId,
  selectedNodeId,
  onSelectNode,
  defaultOpen,
  depth = 0,
  focusedTopicIds = null,
}: TopicBranchProps) {
  const [open, setOpen] = useState(defaultOpen)
  const children = topic.children ?? []
  const childTopics = children.filter((c) => c.type === 'topic')
  const childNodes = children.filter((c) => c.type === 'knowledge_node')

  const isFocusActive = focusedTopicIds !== null
  const isOnFocusPath = isFocusActive && focusedTopicIds!.has(topic.id)
  const isDimmed = isFocusActive && !isOnFocusPath
  // JA: 経路上のTopicは(ユーザーが折りたたんでいても)強制的に開く。
  //     経路外はユーザーの手動開閉(open)をそのまま尊重する。
  // VI: Topic trên đường dẫn thì luôn ép mở (kể cả khi user đã gấp lại).
  //     Ngoài đường dẫn thì tôn trọng trạng thái đóng/mở (open) user tự bấm.
  const effectiveOpen = isOnFocusPath || open

  return (
    <div
      className={`transition-all duration-200 ${depth > 0 ? 'border-l border-slate-100 pl-4' : ''} ${
        isDimmed ? 'scale-[0.97] opacity-35 saturate-50' : 'scale-100 opacity-100'
      }`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-xl border-0 bg-transparent px-2 py-1.5 text-left text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        <ChevronRight
          className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform ${effectiveOpen ? 'rotate-90' : ''}`}
        />
        <FolderTree className={`h-4 w-4 shrink-0 ${isOnFocusPath ? 'text-teal-600' : 'text-teal-600/70'}`} />
        <span>{topic.label}</span>
      </button>

      {effectiveOpen && (
        <div className="mt-1 space-y-1 pl-2">
          {childNodes.map((node) => (
            <KnowledgeLeaf
              key={node.id}
              node={node}
              schedule={scheduleByNodeId.get(node.id)}
              isSelected={selectedNodeId === node.id}
              onSelect={onSelectNode}
              // JA: 経路上のTopic内でも、選択されていない兄弟の葉は少し控えめにする
              //     (選択中の葉が兄弟の中でも際立つように)。
              // VI: Trong Topic nằm trên đường dẫn, lá anh em chưa được chọn cũng
              //     làm mờ nhẹ (để lá đang chọn nổi bật hơn giữa các anh em).
              isDimmed={isFocusActive && selectedNodeId !== node.id}
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
              focusedTopicIds={focusedTopicIds}
            />
          ))}
        </div>
      )}
    </div>
  )
}
