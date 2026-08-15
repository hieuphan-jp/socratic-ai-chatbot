/**
 * features/hintChat/components/StepTreeFlow.tsx
 *
 * JA: Dagreアルゴリズムを使用して思考ツリーを自動レイアウト表示するコンポーネント。
 * VI: Component hiển thị sơ đồ tư duy với layout tự động bằng thuật toán Dagre.
 */

import React, { useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

import { StepNodeCard } from './StepNodeCard';
import type { StepNode } from '../types';

interface StepTreeFlowProps {
  stepNodes?: StepNode[]; // Thêm '?' để tránh bắt buộc
}

// JA: Dagreアルゴリズムによるノード位置の自動計算
// VI: Hàm tự động tính toán vị trí Node bằng thuật toán Dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const nodeWidth = 260;
  const nodeHeight = 100;

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 80,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

const StepTreeFlowInner: React.FC<StepTreeFlowProps> = ({ stepNodes = [] }) => {
  const nodeTypes = useMemo(() => ({ stepNodeCard: StepNodeCard }), []);

  // 1. JA: ノードの初期化（stepNodesがundefinedの場合でも空配列で安全に処理）
  // VI: Khởi tạo dữ liệu cho Nodes (An toàn kể cả khi stepNodes bị undefined)
  const rawNodes: Node[] = useMemo(() => {
    const safeNodes = stepNodes || [];
    return safeNodes.map((step) => ({
      id: step.id,
      type: 'stepNodeCard',
      data: step,
      position: { x: 0, y: 0 },
    }));
  }, [stepNodes]);

  // 2. JA: エッジの初期化
  // VI: Khởi tạo dữ liệu cho Edges
  const rawEdges: Edge[] = useMemo(() => {
    const safeNodes = stepNodes || [];
    if (safeNodes.length < 2) return [];

    return safeNodes.slice(0, -1).map((step, index) => {
      const nextStep = safeNodes[index + 1];
      const isCompleted = step.status === 'completed';
      const isInProgress = nextStep.status === 'in_progress';

      return {
        id: `e-${step.id}-${nextStep.id}`,
        source: step.id,
        target: nextStep.id,
        animated: isInProgress,
        style: {
          stroke: isCompleted ? '#10b981' : '#94a3b8',
          strokeWidth: 2,
        },
      };
    });
  }, [stepNodes]);

  // 3. JA: 自動レイアウト適用 / VI: Áp dụng tự động sắp xếp layout
  const { nodes, edges } = useMemo(() => {
    return getLayoutedElements(rawNodes, rawEdges, 'TB');
  }, [rawNodes, rawEdges]);

  return (
    <div className="w-full h-full bg-slate-50/50 rounded-3xl border border-slate-200 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.4 }}
        attributionPosition="bottom-right"
        defaultEdgeOptions={{
          type: 'smoothstep',
        }}
      >
        <Background color="#cbd5e1" variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls className="!bg-white !border-slate-200 !shadow-sm !rounded-xl overflow-hidden" />
      </ReactFlow>
    </div>
  );
};

// JA: ReactFlowProviderでラップしたエクスポート用コンポーネント
// VI: Component bọc ReactFlowProvider để tránh lỗi context của React Flow
export const StepTreeFlow: React.FC<StepTreeFlowProps> = (props) => (
  <ReactFlowProvider>
    <StepTreeFlowInner {...props} />
  </ReactFlowProvider>
);