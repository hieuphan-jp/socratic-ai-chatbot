/**
 * features/hintChat/utils/stepTreeLayout.ts
 *
 * JA: 思考ツリーの配置。大ステップ(step1,2,3...)は下から上へまっすぐ伸びる幹。
 *     そこから枝分かれ(is_branch)したステップ(例: step2-1)は、分岐した瞬間の
 *     方向から斜めにずれた方向へ伸びる。さらにその枝から枝分かれしたものも、
 *     「そのとき自分が向いている方向」からさらに斜め前へずれる(方向を毎回リセット
 *     して垂直に戻したりはしない)。枝分かれではない継続(is_branch=false)は、
 *     常に「今向いている方向」のままま真っ直ぐ伸びる。
 *     ★以前は dagre(rankdir: 'BT')に丸投げしていたが、dagre は段ごとの重なり回避は
 *     やってくれても「枝は斜めに」という向きの指定はできないため、方向ベクトルを
 *     自前で引き継ぐ再帰配置に書き換えた。
 * VI: Bố trí cây tư duy. Bước lớn (step1,2,3...) là thân cây, mọc thẳng từ dưới lên.
 *     Bước rẽ nhánh (is_branch, vd step2-1) mọc lệch theo hướng chéo tính từ hướng
 *     tại đúng điểm rẽ nhánh đó. Nhánh rẽ tiếp từ nhánh đó cũng lệch chéo tiếp từ
 *     "hướng hiện tại của chính nó" (không reset về thẳng đứng). Bước tiếp diễn
 *     không rẽ nhánh (is_branch=false) luôn đi thẳng theo đúng hướng hiện tại.
 *     ★Trước đây giao hết cho dagre (rankdir: 'BT'). Dagre tránh chồng lấn theo hàng
 *     tốt, nhưng không thể chỉ định "nhánh phải chéo", nên đổi sang tự tính hướng
 *     bằng đệ quy.
 */
import type { Node, Edge } from '@xyflow/react'

import type { FlowNode, FlowEdge } from '@/shared/types'

export const LEAF_WIDTH = 176
export const LEAF_HEIGHT = 60

// JA: 幹(継続)1歩ぶんの距離。 VI: Khoảng cách 1 bước của thân (tiếp diễn, không rẽ nhánh).
const TRUNK_STEP_LENGTH = 124
// JA: 枝分かれした瞬間の1歩だけ長めにする(幹の次のノードと重ならないようにするため)。
// VI: Riêng bước đầu tiên ngay lúc rẽ nhánh thì dài hơn (để không đè lên node tiếp theo của thân).
const BRANCH_STEP_LENGTH = 280
// JA: 分岐で逸れる角度。 VI: Góc lệch khi rẽ nhánh.
const BRANCH_ANGLE_DEG = 45
// JA: 同じノードから複数枝分かれする時、2本目以降をさらに開くための倍率(左右交互)。
// VI: Khi 1 node rẽ nhiều nhánh, hệ số mở rộng thêm cho nhánh thứ 2 trở đi (xen kẽ trái/phải).
const BRANCH_FAN_GROWTH = 1.8

type Placed = { x: number; y: number; direction: number }

const toRad = (deg: number) => (deg * Math.PI) / 180

export function layoutStepTree(flowNodes: FlowNode[], flowEdges: FlowEdge[]): { nodes: Node[]; edges: Edge[] } {
  const nodeIds = new Set(flowNodes.map((n) => n.id))
  const childEdgesByParent = new Map<string, FlowEdge[]>()
  for (const e of flowEdges) {
    if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) continue
    const list = childEdgesByParent.get(e.source) ?? []
    list.push(e)
    childEdgesByParent.set(e.source, list)
  }

  const targets = new Set(flowEdges.map((e) => e.target))
  const rootId = flowNodes.find((n) => !targets.has(n.id))?.id ?? flowNodes[0]?.id

  const placed = new Map<string, Placed>()
  const visited = new Set<string>()

  function place(id: string, x: number, y: number, direction: number) {
    if (visited.has(id)) return
    visited.add(id)
    placed.set(id, { x, y, direction })

    let branchIndex = 0
    for (const edge of childEdgesByParent.get(id) ?? []) {
      if (edge.is_branch) {
        const sign = branchIndex % 2 === 0 ? 1 : -1
        const spread = BRANCH_FAN_GROWTH ** Math.floor(branchIndex / 2)
        const childDirection = direction + sign * BRANCH_ANGLE_DEG * spread
        const rad = toRad(childDirection)
        place(edge.target, x + BRANCH_STEP_LENGTH * Math.sin(rad), y - BRANCH_STEP_LENGTH * Math.cos(rad), childDirection)
        branchIndex += 1
      } else {
        const rad = toRad(direction)
        place(edge.target, x + TRUNK_STEP_LENGTH * Math.sin(rad), y - TRUNK_STEP_LENGTH * Math.cos(rad), direction)
      }
    }
  }

  if (rootId) place(rootId, 0, 0, 0)

  const nodes: Node[] = flowNodes.map((n) => {
    const pos = placed.get(n.id) ?? { x: 0, y: 0, direction: 0 }
    return {
      id: n.id,
      type: 'stepLeaf',
      data: { ...n.data },
      // JA: 基準点は中心なので、React Flowが期待する左上座標へ変換する。
      // VI: Điểm chuẩn là tâm, cần đổi sang tọa độ góc trên-trái mà React Flow cần.
      position: { x: pos.x - LEAF_WIDTH / 2, y: pos.y - LEAF_HEIGHT / 2 },
    }
  })

  const edges: Edge[] = flowEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    // JA: 斜めの枝には smoothstep(直角基調)が合わないため直線にする。
    // VI: smoothstep (dựa theo góc vuông) không hợp với cành chéo, nên dùng đường thẳng.
    type: 'straight',
    animated: !e.is_branch,
    style: {
      stroke: e.is_branch ? '#d9c3a1' : '#b08d5b',
      strokeWidth: e.is_branch ? 1.75 : 2.5,
      strokeDasharray: e.is_branch ? '4 3' : undefined,
    },
  }))

  return { nodes, edges }
}
