import React, { useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';

import { StepNodeCard } from './StepNodeCard';
import type { StepNode } from '../types';

interface StepTreeFlowProps {
  stepNodes: StepNode[];
}

// Hàm tự động tính toán vị trí Node bằng thuật toán Dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  // Kích thước ước tính của Node (Width x Height)
  const nodeWidth = 260;
  const nodeHeight = 100;

  // Cấu hình hướng xếp (TB = Top to Bottom) và KHOẢNG CÁCH
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 50,  // Khoảng cách giữa các node cùng hàng
    ranksep: 80,  // Khoảng cách theo chiều dọc giữa các bước (Tăng số này nếu muốn thưa hơn)
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

export const StepTreeFlow: React.FC<StepTreeFlowProps> = ({ stepNodes }) => {
  const nodeTypes = useMemo(() => ({ stepNodeCard: StepNodeCard }), []);

  // 1. Khởi tạo dữ liệu thô cho Nodes & Edges
  const rawNodes: Node[] = useMemo(() => {
    return stepNodes.map((step) => ({
      id: step.id,
      type: 'stepNodeCard',
      data: step,
      position: { x: 0, y: 0 }, // Sẽ do Dagre tính toán lại
    }));
  }, [stepNodes]);

  const rawEdges: Edge[] = useMemo(() => {
    return stepNodes.slice(0, -1).map((step, index) => {
      const nextStep = stepNodes[index + 1];
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

  // 2. Chạy thuật toán Dagre để lấy tọa độ tự động chuẩn xác
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