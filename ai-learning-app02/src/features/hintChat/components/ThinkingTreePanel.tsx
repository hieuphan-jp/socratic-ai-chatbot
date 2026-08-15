/**
 * features/hintChat/components/ThinkingTreePanel.tsx
 *
 * JA: 思考ツリー表示コンポーネント (分岐・Parent-Child 構造対応版 - Clean Typescript)
 * VI: Component Sơ đồ tư duy (Chuẩn Type-safe, không sử dụng `any`)
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

// Khai báo Type mở rộng để hỗ trợ các trường rẽ nhánh từ API Backend nếu ChatMessage chưa có
interface ExtendedChatMessage extends ChatMessage {
  sender_type?: string
  node_type?: string
}

interface ThinkingTreePanelProps {
  messages: ChatMessage[]
}

export const ThinkingTreePanel: React.FC<ThinkingTreePanelProps> = ({ messages }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    const generatedNodes: Node[] = []
    const generatedEdges: Edge[] = []

    // Cast mảng sang ExtendedChatMessage để truy cập an toàn các trường mở rộng
    const extendedMessages = messages as ExtendedChatMessage[]

    // 1. Lọc bỏ các tin nhắn lỗi giới hạn API
    const validMessages = extendedMessages.filter((msg) => {
      const text = msg.message_text || ''
      const isApiLimitError = text.includes('[AiTutor]') && text.includes('bị giới hạn')
      return !isApiLimitError
    })

    // 2. Chỉ giữ lại tin nhắn USER đã có câu trả lời AI đi kèm
    const userMsgs = validMessages.filter((msg, index) => {
      const sender = (msg.sender || msg.node_type || msg.sender_type || '').toUpperCase()
      const isUser = sender === 'USER' || sender === 'HUMAN'

      if (!isUser) return false

      const hasAiResponseAfter = validMessages.slice(index + 1).some((nextMsg) => {
        const nextSender = (nextMsg.sender || nextMsg.node_type || nextMsg.sender_type || '').toUpperCase()
        return nextSender === 'AI' || nextSender === 'ASSISTANT' || nextSender === 'BOT'
      })

      return hasAiResponseAfter
    })

    if (userMsgs.length === 0) {
      // Dữ liệu mặc định ban đầu
      generatedNodes.push(
        {
          id: 'step-1',
          data: { label: 'ステップ1: 問題の分析 / Bước 1: Phân tích bài toán' },
          position: { x: 30, y: 20 },
          className:
            '!border !border-blue-300 !rounded-lg !p-2 !text-[11px] !text-center !bg-white !shadow-sm !w-[160px] !cursor-grab active:!cursor-grabbing',
        },
        {
          id: 'step-2',
          data: { label: 'ステップ2: 解法の選択 / Bước 2: Chọn phương pháp' },
          position: { x: 30, y: 110 },
          className:
            '!border !border-gray-300 !rounded-lg !p-2 !text-[11px] !text-center !bg-white !shadow-sm !w-[160px] !cursor-grab active:!cursor-grabbing',
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
      // Map lưu vị trí index của từng user message theo ID
      const nodeIndexMap: Record<string, number> = {}
      userMsgs.forEach((msg, idx) => {
        if (msg.id) nodeIndexMap[String(msg.id).toLowerCase()] = idx
      })

      userMsgs.forEach((msg: ExtendedChatMessage, idx: number) => {
        const text = msg.message_text || ''
        const stepNum = idx + 1
        const nodeId = String(msg.id || `node-${stepNum}`).toLowerCase()

        // Trích xuất parentId hoàn toàn chuẩn type, không qua any
        const rawParent = msg.parent_message_id ?? msg.parent_message
        let parentId: string | null = null

        if (typeof rawParent === 'object' && rawParent !== null && 'id' in rawParent) {
          parentId = String(rawParent.id).toLowerCase()
        } else if (typeof rawParent === 'string' || typeof rawParent === 'number') {
          parentId = String(rawParent).toLowerCase()
        }

        // 🔥 THUẬT TOÁN RẼ NHÁNH: Kiểm tra xem node có rẽ nhánh từ node cũ hơn hay không
        const isBranching = Boolean(
          parentId &&
          nodeIndexMap[parentId] !== undefined &&
          nodeIndexMap[parentId] < idx - 1
        )

        // Nếu rẽ nhánh -> Đẩy sang trục X = 200, nếu không -> Trục X = 30
        const posX = isBranching ? 200 : 30
        const posY = 20 + idx * 90

        generatedNodes.push({
          id: nodeId,
          data: {
            label: `ステップ${stepNum}: ${
              text.length > 15 ? text.substring(0, 15) + '...' : text
            }`,
          },
          position: { x: posX, y: posY },
          draggable: true,
          className: `!rounded-lg !p-2 !text-[11px] !text-center !shadow-sm !w-[160px] !cursor-grab active:!cursor-grabbing ${
            isBranching
              ? '!border-2 !border-blue-600 !bg-blue-50'
              : '!border !border-blue-300 !bg-white'
          }`,
        })

        if (idx > 0) {
          const actualParentId =
            parentId && nodeIndexMap[parentId] !== undefined
              ? parentId
              : String(userMsgs[idx - 1].id).toLowerCase()

          if (actualParentId) {
            generatedEdges.push({
              id: `edge-${idx}`,
              source: actualParentId,
              target: nodeId,
              animated: true,
              style: {
                stroke: isBranching ? '#2563eb' : '#3b82f6',
                strokeDasharray: isBranching ? '0' : '4',
                strokeWidth: isBranching ? 2 : 1.5,
              },
            })
          }
        }
      })
    }

    setNodes(generatedNodes)
    setEdges(generatedEdges)
  }, [messages, setNodes, setEdges])

  return (
    <div className="flex h-full w-full flex-col rounded-2xl border border-gray-200 bg-white p-3 box-border shadow-sm overflow-hidden">
      <div className="mb-2 flex items-center justify-between px-1">
        <h3 className="m-0 text-xs font-bold text-gray-800 truncate">
          🌿 思考プロセス / Tiến trình tư duy
        </h3>
        <span className="text-[10px] text-gray-400">
          🖐️ ドラッグ可能 / Rê chuột di chuyển
        </span>
      </div>

      <div className="w-full flex-1 rounded-lg border border-gray-100 overflow-hidden relative min-h-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodesDraggable={true}
          nodesConnectable={false}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={10} size={1} color="#d1d5db" />
          <Controls position="bottom-left" showInteractive={true} />
        </ReactFlow>
      </div>
    </div>
  )
}