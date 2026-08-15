/**
 * features/hintChat/utils/flowMapper.ts
 *
 * JA: StepNode 配列や ChatMessage 配列を React Flow の Node と Edge に変換するマッパー。
 * VI: Hàm mapper chuyển đổi mảng StepNode hoặc ChatMessage sang nodes và edges dùng cho React Flow.
 */

import type { Node, Edge } from '@xyflow/react'
import type { StepNode, ChatMessage } from '../types'

/**
 * JA: StepNode配列をReact Flow用のnodesとedgesに変換するヘルパー関数。
 * VI: Hàm helper chuyển đổi mảng StepNode sang nodes và edges dùng cho React Flow.
 */
export function mapStepNodesToFlow(stepNodes: StepNode[]): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // JA: Y軸とX軸のノード間隔 / VI: Khoảng cách giữa các node trên trục Y và X
  const Y_OFFSET = 90
  const X_OFFSET = 220

  stepNodes.forEach((step, index) => {
    // 1. JA: 表示ノードの作成 / VI: Tạo Node hiển thị
    nodes.push({
      id: step.id,
      position: { 
        x: step.parentId ? X_OFFSET : 50, 
        y: index * Y_OFFSET + 20 
      },
      data: { label: step.label },
      style: {
        borderRadius: '8px',
        padding: '10px 14px',
        fontSize: '12px',
        border: '1px solid #cbd5e1',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      },
    })

    // 2. JA: parentIdが存在する場合、エッジ（接続線）を作成 / VI: Tạo Edge nếu node này có parentId
    if (step.parentId) {
      edges.push({
        id: `edge-${step.parentId}-${step.id}`,
        source: step.parentId,
        target: step.id,
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 2 },
      })
    }
  })

  return { nodes, edges }
}

/**
 * JA: ChatMessage 配列から動的に React Flow の Node と Edge を計算して生成するヘルパー関数。
 * VI: Hàm helper tính toán Node và Edge từ danh sách tin nhắn chat.
 */
export function mapMessagesToFlow(messages: ChatMessage[]): { nodes: Node[]; edges: Edge[] } {
  const userMsgs = messages.filter((msg) => msg.sender === 'user')

  if (userMsgs.length === 0) {
    return mapStepNodesToFlow([
      { id: 'step-1', label: 'Bước 1: Phân tích bài toán' },
      { id: 'step-2', label: 'Bước 2: Chọn phương pháp giải' },
    ])
  }

  const stepNodes: StepNode[] = userMsgs.map((msg, idx) => ({
    id: msg.id || `node-${idx + 1}`,
    label: `Bước ${idx + 1}: ${msg.text.length > 18 ? `${msg.text.substring(0, 18)}...` : msg.text}`,
  }))

  return mapStepNodesToFlow(stepNodes)
}