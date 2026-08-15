/**
 * features/hintChat/components/ThinkingTreePanel.tsx
 *
 * JA: 思考ツリー表示コンポーネント (ノードドラッグ移動対応 / 日英対応)
 * VI: Component hiển thị Sơ đồ tư duy (Cho phép kéo thả di chuyển node / Hỗ trợ Việt - Nhật)
 */

import React, { useEffect } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { ChatMessage } from '@/shared/types'

interface ThinkingTreePanelProps {
  messages: ChatMessage[]
}

export const ThinkingTreePanel: React.FC<ThinkingTreePanelProps> = ({ messages }) => {
  // Dùng useNodesState & useEdgesState để ReactFlow tự quản lý vị trí khi người dùng drag/drop
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  // Lắng nghe thay đổi của messages để cập nhật danh sách node
  useEffect(() => {
    const generatedNodes: Node[] = []
    const generatedEdges: Edge[] = []

    const userMsgs = messages.filter((msg) => {
      const sender = (msg.sender || msg.node_type || '').toUpperCase()
      return sender === 'USER' || sender === 'HUMAN'
    })

    if (userMsgs.length === 0) {
      // Node mặc định ban đầu
      generatedNodes.push(
        {
          id: 'step-1',
          data: { label: 'ステップ1: 問題の分析 / Bước 1: Phân tích bài toán' },
          position: { x: 40, y: 30 },
          draggable: true,
          className:
            '!border !border-blue-300 !rounded-lg !p-2.5 !text-[11px] !text-center !bg-white !shadow-sm !w-[180px] !cursor-grab active:!cursor-grabbing',
        },
        {
          id: 'step-2',
          data: { label: 'ステップ2: 解法の選択 / Bước 2: Chọn phương pháp' },
          position: { x: 40, y: 130 },
          draggable: true,
          className:
            '!border !border-gray-300 !rounded-lg !p-2.5 !text-[11px] !text-center !bg-white !shadow-sm !w-[180px] !cursor-grab active:!cursor-grabbing',
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

        generatedNodes.push({
          id: nodeId,
          data: {
            label: `ステップ${stepNum}: ${
              text.length > 15 ? text.substring(0, 15) + '...' : text
            } / Bước ${stepNum}`,
          },
          position: { x: 40, y: 30 + idx * 95 },
          draggable: true, // Cho phép kéo thả
          className:
            '!border !border-blue-400 !rounded-lg !p-2.5 !text-[11px] !text-center !bg-white !shadow-sm !w-[180px] !cursor-grab active:!cursor-grabbing',
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

    setNodes(generatedNodes)
    setEdges(generatedEdges)
  }, [messages, setNodes, setEdges])

  return (
    <div className="flex h-[480px] w-full flex-col rounded-2xl border border-gray-200 bg-white p-3 box-border shadow-sm">
      {/* Header Panel */}
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="m-0 text-xs font-bold text-gray-800">
          🌿 思考プロセス / Tiến trình tư duy
        </h3>
        <span className="text-[10px] text-gray-400">
          🖐️ ドラッグ可能 / Rê chuột để di chuyển node
        </span>
      </div>

      {/* Khung ReactFlow */}
      <div className="w-full flex-1 rounded-lg border border-gray-100 overflow-hidden relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange} // Giúp cập nhật tọa độ mới khi kéo
          onEdgesChange={onEdgesChange}
          nodesDraggable={true}
          nodesConnectable={false}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#d1d5db" />
          <Controls position="bottom-left" showInteractive={true} />
        </ReactFlow>
      </div>
    </div>
  )
}