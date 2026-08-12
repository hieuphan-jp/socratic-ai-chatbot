import type { Node, Edge } from '@xyflow/react'
import type { StepNode } from '@/shared/types'

/**
 * JA: StepNode配列をReact Flow用のnodesとedgesに変換するヘルパー関数。
 * VI: Hàm helper chuyển đổi mảng StepNode sang nodes và edges dùng cho React Flow.
 */
export function mapStepNodesToFlow(stepNodes: StepNode[]): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = []
  const edges: Edge[] = []

  // Khoảng cách giữa các node trên trục Y và X
  const Y_OFFSET = 90
  const X_OFFSET = 200

  stepNodes.forEach((step, index) => {
    // 1. Tạo Node hiển thị
    nodes.push({
      id: step.id,
      // Tạm thời sắp xếp các bước dọc xuống (Y) và thụt lề nhẹ nếu là nhánh con (X)
      position: { 
        x: step.parentId ? X_OFFSET : 50, 
        y: index * Y_OFFSET + 20 
      },
      data: { label: step.label },
      // Kiểu style cơ bản cho node
      style: {
        borderRadius: '8px',
        padding: '10px 14px',
        fontSize: '12px',
        border: '1px solid #cbd5e1',
        backgroundColor: '#ffffff',
        boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      },
    })

    // 2. Tạo Edge (đường nối) nếu node này có parentId
    if (step.parentId) {
      edges.push({
        id: `edge-${step.parentId}-${step.id}`,
        source: step.parentId,
        target: step.id,
        animated: true, // Hiệu ứng nét đứt chuyển động phong cách Git/Flow
        style: { stroke: '#6366f1', strokeWidth: 2 }, // Màu đường nối
      })
    }
  })

  return { nodes, edges }
}