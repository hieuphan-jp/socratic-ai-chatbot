/**
 * features/hintChat/components/TopicFolderPicker.tsx
 *
 * JA: 学習木はTopicが入れ子(フォルダ)になっており、末端にKnowledgeNode(ファイル)が
 *     入るPCのフォルダ/ファイルのような構造。このピッカーはその階層をドリルダウンで
 *     辿り、知識ノードの保存先Topicを選ばせる（新しいフォルダの作成にも対応）。
 * VI: Cây học tập có cấu trúc Topic lồng nhau (thư mục), KnowledgeNode (tệp) nằm ở lá
 *     cuối — giống cấu trúc thư mục/tệp trên máy tính. Picker này cho phép duyệt sâu
 *     dần theo cấp bậc để chọn Topic lưu knowledge node (hỗ trợ tạo thư mục mới).
 */
import { useState } from 'react'

import { useTopicFolder, useCreateTopic } from '../api/useChat'
import { Button, Input, Notice, ErrorText } from '@/shared/ui'

type Crumb = { id: string; name: string }

export function TopicFolderPicker({
  onSelect,
  onCancel,
}: {
  onSelect: (topicId: string) => void
  onCancel: () => void
}) {
  // JA: null = ルート直下。breadcrumbはルートから現在地までの経路。
  // VI: null = ở gốc. breadcrumb là đường đi từ gốc tới vị trí hiện tại.
  const [currentId, setCurrentId] = useState<string | null>(null)
  const [breadcrumb, setBreadcrumb] = useState<Crumb[]>([])
  const [newFolderName, setNewFolderName] = useState('')

  const { data, isPending } = useTopicFolder(currentId)
  const createTopicMutation = useCreateTopic()

  const openFolder = (folder: Crumb) => {
    setBreadcrumb((prev) => [...prev, folder]);
    setCurrentId(folder.id);
  }

  const goToBreadcrumb = (index: number) => {
    if (index < 0) {
      setBreadcrumb([]);
      setCurrentId(null);
      return;
    }
    setBreadcrumb((prev) => prev.slice(0, index + 1));
    setCurrentId(breadcrumb[index].id);
  }

  const handleCreateFolder = async () => {
    const name = newFolderName.trim()
    if (!name) return
    await createTopicMutation.mutateAsync({ name, parentId: currentId })
    setNewFolderName('')
  }

  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <div style={{ fontSize: 13, color: '#666' }}>
        <span style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={() => goToBreadcrumb(-1)}>
          ルート / Gốc
        </span>
        {breadcrumb.map((crumb, i) => (
          <span key={crumb.id}>
            {' > '}
            <span style={{ cursor: 'pointer', textDecoration: 'underline' }} onClick={() => goToBreadcrumb(i)}>
              {crumb.name}
            </span>
          </span>
        ))}
      </div>

      {isPending ? (
        <Notice>読み込み中… / Đang tải…</Notice>
      ) : (
        <div style={{ display: 'grid', gap: 4, maxHeight: 200, overflowY: 'auto' }}>
          {(data?.topics.length ?? 0) === 0 && (data?.nodes.length ?? 0) === 0 && (
            <Notice>このフォルダは空です / Thư mục này trống</Notice>
          )}
          {data?.topics.map((topic) => (
            <div
              key={topic.id}
              onClick={() => openFolder({ id: topic.id, name: topic.name })}
              style={{
                cursor: 'pointer',
                padding: '6px 10px',
                borderRadius: 4,
                background: '#f9fafb',
                border: '1px solid #eee',
              }}
            >
              📁 {topic.name}
            </div>
          ))}
          {data?.nodes.map((node) => (
            <div key={node.id} style={{ padding: '6px 10px', color: '#9ca3af' }}>
              📄 {node.title}
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <Input
          placeholder="新しいフォルダ名 / Tên thư mục mới"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          style={{ flex: 1 }}
        />
        <Button
          type="button"
          onClick={handleCreateFolder}
          disabled={!newFolderName.trim() || createTopicMutation.isPending}
        >
          作成 / Tạo
        </Button>
      </div>
      {createTopicMutation.isError && (
        <ErrorText>{(createTopicMutation.error as Error).message}</ErrorText>
      )}

      <div style={{ display: 'flex', gap: 8 }}>
        <Button type="button" onClick={() => currentId && onSelect(currentId)} disabled={!currentId}>
          このフォルダに保存 / Lưu vào thư mục này
        </Button>
        <Button type="button" onClick={onCancel}>
          キャンセル / Hủy
        </Button>
      </div>
    </div>
  )
}
