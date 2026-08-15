/**
 * features/hintChat/components/ThinkingTreePanel.tsx
 *
 * JA: 思考ツリー表示コンポーネント (ReactFlow直挿し版)
 * VI: Component hiển thị Sơ đồ tư duy trực tiếp bằng ReactFlow (Dùng Tailwind CSS & Hỗ trợ Việt - Nhật)
 */

import React, { useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { ChatMessage } from '@/shared/types'

interface ThinkingTreePanelProps {
  messages: ChatMessage[]
}

export const ThinkingTreePanel: React.FC<ThinkingTreePanelProps> = ({ messages }) => {
  // Tính toán Nodes và Edges trực tiếp từ danh sách tin nhắn
  const { nodes, edges } = useMemo(() => {
    const generatedNodes: Node[] = []
    const generatedEdges: Edge[] = []

    const userMsgs = messages.filter((msg) => {
      const sender = (msg.sender || msg.node_type || '').toUpperCase()
      return sender === 'USER' || sender === 'HUMAN'
    })

    if (userMsgs.length === 0) {
      // Node mặc định ban đầu khi chưa gửi tin nhắn
      generatedNodes.push(
        {
          id: 'step-1',
          data: { label: 'ステップ1: 問題の分析 / Bước 1: Phân tích bài toán' },
          position: { x: 40, y: 30 },
          className:
            '!border !border-gray-300 !rounded-md !p-2 !text-[11px] !text-center !bg-white !shadow-sm !w-[170px]',
        },
        {
          id: 'step-2',
          data: { label: 'ステップ2: 解法の選択 / Bước 2: Chọn phương pháp' },
          position: { x: 40, y: 130 },
          className:
            '!border !border-gray-300 !rounded-md !p-2 !text-[11px] !text-center !bg-white !shadow-sm !w-[170px]',
        }
      )

      generatedEdges.push({
        id: 'e1-2',
        source: 'step-1',
        target: 'step-2',
        animated: true,
        style: { stroke: '#3b82f6', strokeDasharray: '4', strokeWidth: 1.5 },
      })
    } else {
      userMsgs.forEach((msg, idx) => {
        const text = msg.message_text || ''
        const stepNum = idx + 1
        const nodeId = String(msg.id || `node-${stepNum}`).toLowerCase()

        // Tính vị trí xếp dọc đơn giản
        const posX = 40
        const posY = 30 + idx * 90

        generatedNodes.push({
          id: nodeId,
          data: {
            label: `ステップ${stepNum}: ${
              text.length > 15 ? text.substring(0, 15) + '...' : text
            } / Bước ${stepNum}`,
          },
          position: { x: posX, y: posY },
          className:
            '!border !border-gray-300 !rounded-md !p-2 !text-[11px] !text-center !bg-white !shadow-sm !w-[170px] !cursor-grab',
        })

        if (idx > 0) {
          const prevNodeId = String(userMsgs[idx - 1].id || `node-${idx}`).toLowerCase()
          generatedEdges.push({
            id: `edge-${idx}`,
            source: prevNodeId,
            target: nodeId,
            animated: true,
            style: { stroke: '#3b82f6', strokeDasharray: '4', strokeWidth: 1.5 },
          })
        }
      })
    }

    return { nodes: generatedNodes, edges: generatedEdges }
  }, [messages])

  return (
    <div className="flex h-[480px] w-full flex-col rounded-2xl border border-gray-200 bg-white p-3 box-border shadow-sm">
      {/* Header Panel */}
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="m-0 text-xs font-bold text-gray-800">
          🌿 思考プロセス / Tiến trình tư duy
        </h3>
        <span className="text-[10px] text-gray-400">✋ Có thể kéo/thả node</span>
      </div>

      {/* Khung ReactFlow */}
      <div className="w-full flex-1 rounded-lg border border-gray-100 overflow-hidden relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          nodesDraggable={true}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#d1d5db" />
          <Controls position="bottom-left" showInteractive={true} />
        </ReactFlow>
      </div>
    </div>
  )
}