/**
 * features/hintChat/utils/stepTreeLayout.ts
 *
 * JA: 思考ツリーを「下から上へ育つ木」として配置する。dagre に rankdir: 'BT'
 *     (Bottom-to-Top) を指定するだけで、幹・枝が自然に下から生えて上に伸びる
 *     配置になる（分岐があっても重なりを自動で避けてくれる）。
 *     ★これ以前は depth*X, index*Y の手計算で、分岐すると重なることがあった。
 * VI: Bố trí cây tư duy như "cây lớn từ dưới lên". Chỉ cần truyền
 *     rankdir: 'BT' (Bottom-to-Top) cho dagre là thân/cành sẽ tự nhiên mọc từ
 *     dưới lên trên (tự tránh chồng lấn kể cả khi có rẽ nhánh).
 *     ★Trước đây tính tay bằng depth*X, index*Y nên rẽ nhánh dễ bị đè lên nhau.
 */
import dagre from 'dagre'
import type { Node, Edge } from '@xyflow/react'

import type { FlowNode, FlowEdge } from '@/shared/types'

export const LEAF_WIDTH = 176
export const LEAF_HEIGHT = 60

export function layoutStepTree(flowNodes: FlowNode[], flowEdges: FlowEdge[]): { nodes: Node[]; edges: Edge[] } {
  const g = new dagre.graphlib.Graph()
  // JA: nodesep=同じ段(枝)同士の間隔、ranksep=段(幹の1節)同士の間隔。
  // VI: nodesep = khoảng cách giữa các node cùng hàng (nhánh), ranksep = khoảng
  //     cách giữa các hàng (một đốt của thân).
  g.setGraph({ rankdir: 'BT', nodesep: 28, ranksep: 64 })
  g.setDefaultEdgeLabel(() => ({}))

  for (const n of flowNodes) {
    g.setNode(n.id, { width: LEAF_WIDTH, height: LEAF_HEIGHT })
  }
  for (const e of flowEdges) {
    g.setEdge(e.source, e.target)
  }

  dagre.layout(g)

  const nodes: Node[] = flowNodes.map((n) => {
    const pos = g.node(n.id)
    return {
      id: n.id,
      type: 'stepLeaf',
      data: { ...n.data },
      // JA: dagreは中心座標を返すので、React Flowが期待する左上座標へ変換する。
      // VI: dagre trả về tọa độ tâm, cần đổi sang tọa độ góc trên-trái mà React Flow cần.
      position: { x: pos.x - LEAF_WIDTH / 2, y: pos.y - LEAF_HEIGHT / 2 },
    }
  })

  const edges: Edge[] = flowEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    animated: !e.is_branch,
    style: {
      stroke: e.is_branch ? '#d9c3a1' : '#b08d5b',
      strokeWidth: e.is_branch ? 1.75 : 2.5,
      strokeDasharray: e.is_branch ? '4 3' : undefined,
    },
  }))

  return { nodes, edges }
}
