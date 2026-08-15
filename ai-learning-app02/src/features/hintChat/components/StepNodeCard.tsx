/**
 * features/hintChat/components/StepNodeCard.tsx
 *
 * JA: 思考ツリー内の各ステップノードを表示するカスタムカードコンポーネント。
 * VI: Custom Card Component hiển thị từng Step Node trong sơ đồ cây tư duy.
 */

import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { CheckCircle2, Clock, Circle } from 'lucide-react';
import type { StepNode } from '../types';

interface StepNodeCardProps {
  data: StepNode;
}

export const StepNodeCard: React.FC<StepNodeCardProps> = ({ data }) => {
  const getStatusBadge = () => {
    switch (data?.status) {
      case 'completed':
        return {
          border: 'border-emerald-300 bg-emerald-50/50 text-emerald-700',
          icon: <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />,
          label: 'Hoàn thành / 完了',
        };
      case 'in_progress':
        return {
          border: 'border-indigo-400 bg-indigo-50/50 text-indigo-700 ring-2 ring-indigo-100',
          icon: <Clock className="w-4 h-4 text-indigo-600 animate-pulse shrink-0" />,
          label: 'Đang làm / 進行中',
        };
      default:
        return {
          border: 'border-slate-200 bg-slate-50/50 text-slate-500',
          icon: <Circle className="w-4 h-4 text-slate-300 shrink-0" />,
          label: 'Chờ / 待機',
        };
    }
  };

  const statusStyle = getStatusBadge();

  return (
    <div className={`relative p-3.5 rounded-2xl border bg-white shadow-sm min-w-[220px] max-w-[280px] transition-all ${statusStyle.border}`}>
      {/* Target Handle: Nối từ Node phía trên đến */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-slate-400 !w-3 !h-3 !border-2 !border-white z-10"
      />

      <div className="flex items-start gap-2.5">
        {statusStyle.icon}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-1 mb-1">
            <span className={`text-[10px] px-2 py-0.5 rounded-md font-medium border ${statusStyle.border}`}>
              {statusStyle.label}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">#{data?.id || ''}</span>
          </div>
          <p className="text-xs font-semibold leading-snug text-slate-800">
            {data?.label || ''}
          </p>
          {data?.labelJp && (
            <p className="text-[10px] text-slate-400 mt-0.5">
              {data.labelJp}
            </p>
          )}
        </div>
      </div>

      {/* Source Handle: Nối từ Node này xuống Node dưới */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-slate-400 !w-3 !h-3 !border-2 !border-white z-10"
      />
    </div>
  );
};