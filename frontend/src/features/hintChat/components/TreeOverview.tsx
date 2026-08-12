/**
 * features/chat/components/TreeOverview.tsx
 *
 * JA: ユーザーが通過した思考ステップ（Gitスタイルのツリー）を表示するコンポーネント。
 * VI: Component hiển thị các bước tư duy người dùng đã đi qua (Sơ đồ dạng Git).
 */

import React from 'react'
import type { StepNode } from '@/shared/types'

type TreeOverviewProps = {
  treeNodes: StepNode[]
}

export const TreeOverview: React.FC<TreeOverviewProps> = ({ treeNodes }) => {
  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        {/* JA: 思考プロセス（Gitツリー） / VI: Tiến trình tư duy (Sơ đồ Git) */}
        <span>🌿</span>
        <span>思考プロセス / Tiến trình tư duy</span>
      </h3>

      <div className="space-y-0 relative pl-4 border-l-2 border-indigo-200 ml-2">
        {treeNodes.map((node) => {
          return (
            <div key={node.id} className="relative pb-5 last:pb-0 pl-4">
              {/* JA: ステップポイント（ドット） / VI: Điểm chấm thể hiện bước */}
              <span className="absolute -left-[21px] top-1 w-3 h-3 rounded-full border-2 border-indigo-500 bg-white" />

              <div className="text-xs font-semibold text-indigo-600">
                ステップ {node.step_number} / Bước {node.step_number}
              </div>
              
              <div className="text-xs text-gray-700 mt-0.5">
                {node.label}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}