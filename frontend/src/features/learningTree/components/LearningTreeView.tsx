/**
 * features/learningTree/components/LearningTreeView.tsx
 *
 * JA: 学習内容を木構造で表示し、キーワード検索でフィルタする画面部品（モック）。
 *     検索にヒットしたノードとその祖先だけを残して表示する。
 * VI: Component hiển thị nội dung đã học dạng cây, lọc theo từ khóa tìm kiếm (mock).
 *     Chỉ giữ lại node khớp tìm kiếm và tổ tiên của nó để hiển thị.
 */
import { useEffect, useMemo, useState } from 'react'

import { ErrorText, Input, Notice } from '@/shared/ui'
import type { TreeNode } from '@/shared/types'

import { useLearningTree } from '../api/hooks'

// JA: keyword を含むノードだけ残した木を作る（親は子が残る限り残す）。
// VI: Tạo lại cây chỉ giữ node chứa keyword (node cha giữ lại nếu còn con).
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

function TreeNodeItem({ node, defaultOpen }: { node: TreeNode; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen)
  useEffect(() => {
    setOpen(defaultOpen)
  }, [defaultOpen])
  const hasChildren = !!node.children && node.children.length > 0

  return (
    <li style={{ marginTop: 4 }}>
      <div
        onClick={() => hasChildren && setOpen((v) => !v)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          cursor: hasChildren ? 'pointer' : 'default',
          padding: '4px 6px',
          borderRadius: 4,
        }}
      >
        {hasChildren && <span style={{ fontSize: 12, color: '#666' }}>{open ? '▼' : '▶'}</span>}
        <span>{node.label}</span>
      </div>
      {hasChildren && open && (
        <ul style={{ listStyle: 'none', margin: 0, paddingLeft: 20 }}>
          {node.children!.map((child) => (
            <TreeNodeItem key={child.id} node={child} defaultOpen={defaultOpen} />
          ))}
        </ul>
      )}
    </li>
  )
}

export function LearningTreeView() {
  const [keyword, setKeyword] = useState('')
  const { data, isPending, isError, error } = useLearningTree()
  const filtered = useMemo(() => (data ? filterTree(data, keyword) : []), [data, keyword])

  if (isPending) return <Notice>読み込み中… / Đang tải…</Notice>
  if (isError) return <ErrorText>{(error as Error).message}</ErrorText>

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <Input
        placeholder="キーワードで検索 / Tìm theo từ khóa"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
        style={{ width: '100%' }}
      />
      {filtered.length === 0 ? (
        <Notice>該当なし / Không tìm thấy</Notice>
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {filtered.map((node) => (
            <TreeNodeItem key={node.id} node={node} defaultOpen={keyword.trim().length > 0} />
          ))}
        </ul>
      )}
    </div>
  )
}
