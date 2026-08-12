/**
 * features/chat/components/TreeOverview.tsx
 *
 * JA: ユーザーが通過した思考ステップ（Gitスタイルのツリー）をReact Flowで視覚化するコンポーネント。
 * VI: Component hiển thị trực quan các bước tư duy người dùng đã đi qua (Sơ đồ dạng Git) bằng React Flow.
 */

import React, { useMemo } from 'react'
import { ReactFlow, Controls, Background } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import type { StepNode } from '@/shared/types'
import { mapStepNodesToFlow } from '../utils/flowMapper'

type TreeOverviewProps = {
  treeNodes: StepNode[]
}

export const TreeOverview: React.FC<TreeOverviewProps> = ({ treeNodes }) => {
  // JA: StepNode配列をReact Flow用のnodes/edges構造に変換
  // VI: Chuyển đổi mảng StepNode sang cấu trúc nodes/edges cho React Flow
  const { nodes, edges } = useMemo(() => mapStepNodesToFlow(treeNodes), [treeNodes])

  return (
    <div className="flex flex-col h-full w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        {/* JA: 思考プロセス（Gitツリー） / VI: Tiến trình tư duy (Sơ đồ Git) */}
        <span>🌿</span>
        <span>思考プロセス / Tiến trình tư duy</span>
      </h3>

      {/* JA: React Flow描画エリア（高さ350px固定） / VI: Khu vực hiển thị React Flow (Cố định chiều cao 350px) */}
      <div style={{ width: '100%', height: '350px' }} className="rounded-md border border-slate-200 bg-white overflow-hidden relative">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          {/* JA: ズーム・移動用コントローラー / VI: Thanh điều khiển zoom/pan */}
          <Controls />
          {/* JA: 背景グリッド模様 / VI: Lưới nền dạng chấm */}
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  )
}