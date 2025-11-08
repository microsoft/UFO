import React, { useEffect } from 'react';
import ReactFlow, {
  Background,
  Controls,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  MarkerType,
  NodeTypes,
  Node,
  Edge,
  NodeProps,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DagEdge, DagNode } from '../../store/galaxyStore';

interface DagPreviewProps {
  nodes: DagNode[];
  edges: DagEdge[];
  onSelectNode?: (nodeId: string) => void;
}

const statusColors: Record<string, { bg: string; border: string; text: string; shadow: string }> = {
  pending: {
    bg: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
    border: 'rgba(148, 163, 184, 0.3)',
    text: '#cbd5e1',
    shadow: 'rgba(148, 163, 184, 0.4)',
  },
  running: {
    bg: 'linear-gradient(135deg, #0c4a6e 0%, #0369a1 100%)',
    border: 'rgba(56, 189, 248, 0.5)',
    text: '#bae6fd',
    shadow: 'rgba(56, 189, 248, 0.6)',
  },
  completed: {
    bg: 'linear-gradient(135deg, #14532d 0%, #166534 100%)',
    border: 'rgba(74, 222, 128, 0.5)',
    text: '#bbf7d0',
    shadow: 'rgba(74, 222, 128, 0.6)',
  },
  failed: {
    bg: 'linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%)',
    border: 'rgba(248, 113, 113, 0.5)',
    text: '#fecaca',
    shadow: 'rgba(248, 113, 113, 0.6)',
  },
  skipped: {
    bg: 'linear-gradient(135deg, #713f12 0%, #92400e 100%)',
    border: 'rgba(250, 204, 21, 0.5)',
    text: '#fef3c7',
    shadow: 'rgba(250, 204, 21, 0.6)',
  },
};

type StarNodeData = {
  label: string;
  status?: string;
  taskId: string;
};

const nodeTypes: NodeTypes = {
  star: ({ data }: NodeProps<StarNodeData>) => {
    const colors = statusColors[data.status ?? 'pending'] ?? statusColors.pending;
    return (
      <div className="relative w-[280px]">
        <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
        <div
          className="rounded-2xl border-2 px-5 py-4 text-left shadow-2xl backdrop-blur-sm"
          style={{
            background: colors.bg,
            borderColor: colors.border,
            boxShadow: `0 20px 40px -20px ${colors.shadow}, 0 0 0 1px ${colors.border}`,
          }}
        >
          <div 
            className="text-sm font-semibold uppercase tracking-wider mb-2"
            style={{ color: colors.text, opacity: 0.85 }}
          >
            {data.taskId}
          </div>
          <div 
            className="text-lg font-bold leading-snug"
            style={{ color: colors.text }}
          >
            {data.label}
          </div>
        </div>
      </div>
    );
  },
};

const computeDagLayout = (nodes: DagNode[], edges: DagEdge[]) => {
  const nodeIds = new Set(nodes.map((node) => node.id));
  const incoming = new Map<string, number>();
  const adjacency = new Map<string, string[]>();

  nodes.forEach((node) => {
    incoming.set(node.id, 0);
    adjacency.set(node.id, []);
  });

  edges.forEach((edge) => {
    if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
      return;
    }
    incoming.set(edge.target, (incoming.get(edge.target) ?? 0) + 1);
    adjacency.get(edge.source)?.push(edge.target);
  });

  const queue: string[] = [];
  const levels = new Map<string, number>();

  incoming.forEach((count, id) => {
    if (count === 0) {
      queue.push(id);
      levels.set(id, 0);
    }
  });

  const visited = new Set<string>();

  while (queue.length > 0) {
    const current = queue.shift() as string;
    visited.add(current);
    const currentLevel = levels.get(current) ?? 0;

    (adjacency.get(current) ?? []).forEach((target) => {
      const nextLevel = Math.max((levels.get(target) ?? 0), currentLevel + 1);
      levels.set(target, nextLevel);

      const nextIncoming = (incoming.get(target) ?? 0) - 1;
      incoming.set(target, nextIncoming);
      if (nextIncoming <= 0 && !visited.has(target)) {
        queue.push(target);
      }
    });
  }

  nodes.forEach((node) => {
    if (!levels.has(node.id)) {
      levels.set(node.id, 0);
    }
  });

  const groupedByLevel = new Map<number, DagNode[]>();
  nodes.forEach((node) => {
    const level = levels.get(node.id) ?? 0;
    if (!groupedByLevel.has(level)) {
      groupedByLevel.set(level, []);
    }
    groupedByLevel.get(level)!.push(node);
  });

  const columnSpacing = 320;
  const rowSpacing = 180;

  const positions = new Map<string, { x: number; y: number }>();

  Array.from(groupedByLevel.entries())
    .sort(([a], [b]) => a - b)
    .forEach(([level, levelNodes]) => {
      const sorted = levelNodes.sort((a, b) => a.label.localeCompare(b.label));
      const count = sorted.length;
      const totalHeight = (count - 1) * rowSpacing;
      const startY = totalHeight > 0 ? -(totalHeight / 2) : 0;

      sorted.forEach((node, index) => {
        positions.set(node.id, {
          x: level * columnSpacing,
          y: startY + index * rowSpacing,
        });
      });
    });

  return positions;
};

const buildNodes = (nodes: DagNode[], edges: DagEdge[]): Node<StarNodeData>[] => {
  const positions = computeDagLayout(nodes, edges);
  return nodes.map((node) => {
    const position = positions.get(node.id) ?? { x: 0, y: 0 };
    return {
      id: node.id,
      type: 'star',
      data: {
        label: node.label,
        status: node.status,
        taskId: node.id,
      },
      position,
      draggable: false,
      connectable: false,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    };
  });
};

const buildEdges = (edges: DagEdge[]): Edge[] =>
  edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: 'smoothstep',
    animated: false,
    style: {
      stroke: 'rgba(100, 181, 246, 0.6)',
      strokeWidth: 2.5,
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: 'rgba(100, 181, 246, 0.8)',
      width: 18,
      height: 18,
    },
  }));

const DagPreviewInner: React.FC<DagPreviewProps> = ({ nodes, edges, onSelectNode }) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState(buildNodes(nodes, edges));
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(buildEdges(edges));

  useEffect(() => {
    setNodes(buildNodes(nodes, edges));
    setEdges(buildEdges(edges));
  }, [edges, nodes, setEdges, setNodes]);

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      fitViewOptions={{ padding: 0.15, minZoom: 0.75, maxZoom: 1.5 }}
      onNodeClick={(_, node) => onSelectNode?.(node.id)}
      panOnScroll
      zoomOnScroll={true}
      nodesDraggable={false}
      nodesConnectable={false}
      proOptions={{ hideAttribution: true }}
      className="rounded-2xl border border-white/5 bg-black/40"
      style={{ height: '100%', minHeight: 260 }}
    >
      <Controls showInteractive={false} position="bottom-left" />
      <Background gap={24} size={1.5} color="rgba(100, 116, 139, 0.25)" />
    </ReactFlow>
  );
};

const DagPreview: React.FC<DagPreviewProps> = (props) => (
  <ReactFlowProvider>
    <DagPreviewInner {...props} />
  </ReactFlowProvider>
);

export default DagPreview;
