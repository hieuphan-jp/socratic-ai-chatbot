/**
 * features/learningTree/lib/treeFocus.ts
 *
 * JA: 選択中の葉(知識ノード)から根までの祖先Topic idを集める。フォーカスモード
 *     ―「選択したノードへの経路だけを開いたまま見せ、それ以外は暗く・折り
 *     たたんで縮小する」―のために使う。学習内容ツリーは深いフォルダ階層に
 *     なり得るため、選択に無関係な枝を静かにしてノード数が増えても迷わない
 *     ようにする。
 * VI: Thu thập id các Topic tổ tiên từ lá (knowledge node) đang chọn tới gốc.
 *     Dùng cho chế độ focus — "chỉ giữ mở đường dẫn tới node đã chọn, phần còn
 *     lại làm mờ và gấp lại thu nhỏ". Cây nội dung đã học có thể phân cấp sâu,
 *     nên làm im các nhánh không liên quan để không bị rối khi số node tăng lên.
 */
import type { TreeNode } from '@/shared/types'

export function findAncestorTopicIds(nodes: TreeNode[], targetNodeId: string): Set<string> | null {
  for (const node of nodes) {
    if (node.type === 'knowledge_node' && node.id === targetNodeId) {
      return new Set()
    }
    if (node.type === 'topic' && node.children) {
      const found = findAncestorTopicIds(node.children, targetNodeId)
      if (found) {
        found.add(node.id)
        return found
      }
    }
  }
  return null
}
