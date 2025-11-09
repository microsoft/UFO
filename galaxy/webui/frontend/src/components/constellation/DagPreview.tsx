import React, { useEffect, useRef } from 'react';
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
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { DagNode, DagEdge } from '../../store/galaxyStore';
import { Loader2, CheckCircle2, XCircle, Clock, CircleDashed } from 'lucide-react';

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

/**
 * Get animated status icon for task
 */
const getStatusIcon = (status?: string) => {
  if (!status) {
    return <CircleDashed className="h-4 w-4" />;
  }
  
  const normalized = status.toLowerCase();
  
  if (normalized === 'running' || normalized === 'in_progress') {
    return <Loader2 className="h-4 w-4 animate-spin" />;
  }
  
  if (normalized === 'completed' || normalized === 'success' || normalized === 'finish') {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  
  if (normalized === 'failed' || normalized === 'error') {
    return <XCircle className="h-4 w-4" />;
  }
  
  if (normalized === 'pending' || normalized === 'waiting') {
    return <Clock className="h-4 w-4 animate-pulse" />;
  }
  
  if (normalized === 'skipped') {
    return <CircleDashed className="h-4 w-4" />;
  }
  
  return <CircleDashed className="h-4 w-4" />;
};

type StarNodeData = {
  label: string;
  status?: string;
  taskId: string;
};

const nodeTypes: NodeTypes = {
  star: ({ data }: NodeProps<StarNodeData>) => {
    const colors = statusColors[data.status ?? 'pending'] ?? statusColors.pending;
    const statusIcon = getStatusIcon(data.status);
    
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
          {/* Status icon badge in top-right corner */}
          <div 
            className="absolute -top-2 -right-2 flex items-center justify-center rounded-full border-2 p-1.5 shadow-lg backdrop-blur-sm"
            style={{ 
              background: colors.bg,
              borderColor: colors.border,
              color: colors.text,
            }}
          >
            {statusIcon}
          </div>
          
          <div 
            className="text-xl font-semibold uppercase tracking-wider mb-2"
            style={{ color: colors.text, opacity: 0.85 }}
          >
            {data.taskId}
          </div>
          <div 
            className="text-2xl font-bold leading-snug"
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
  const outgoing = new Map<string, number>();
  const adjacency = new Map<string, string[]>();
  const reverseAdjacency = new Map<string, string[]>();

  nodes.forEach((node) => {
    incoming.set(node.id, 0);
    outgoing.set(node.id, 0);
    adjacency.set(node.id, []);
    reverseAdjacency.set(node.id, []);
  });

  edges.forEach((edge) => {
    if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) {
      return;
    }
    incoming.set(edge.target, (incoming.get(edge.target) ?? 0) + 1);
    outgoing.set(edge.source, (outgoing.get(edge.source) ?? 0) + 1);
    adjacency.get(edge.source)?.push(edge.target);
    reverseAdjacency.get(edge.target)?.push(edge.source);
  });

  // 使用拓扑排序计算层级
  const queue: string[] = [];
  const levels = new Map<string, number>();

  incoming.forEach((count, id) => {
    if (count === 0) {
      queue.push(id);
      levels.set(id, 0);
    }
  });

  const tempIncoming = new Map(incoming);

  while (queue.length > 0) {
    const current = queue.shift() as string;
    const currentLevel = levels.get(current) ?? 0;

    (adjacency.get(current) ?? []).forEach((target) => {
      const nextLevel = Math.max((levels.get(target) ?? 0), currentLevel + 1);
      levels.set(target, nextLevel);

      const nextIncoming = (tempIncoming.get(target) ?? 0) - 1;
      tempIncoming.set(target, nextIncoming);
      if (nextIncoming === 0) {
        queue.push(target);
      }
    });
  }

  // 确保所有节点都有层级
  nodes.forEach((node) => {
    if (!levels.has(node.id)) {
      levels.set(node.id, 0);
    }
  });

  // 按层级分组
  const groupedByLevel = new Map<number, DagNode[]>();
  nodes.forEach((node) => {
    const level = levels.get(node.id) ?? 0;
    if (!groupedByLevel.has(level)) {
      groupedByLevel.set(level, []);
    }
    groupedByLevel.get(level)!.push(node);
  });

  // 增加间距，减少拥挤
  const columnSpacing = 400;  // 水平间距：层级之间的距离（增加此值让节点更分散）
  const baseRowSpacing = 150; // 垂直间距：同一层级节点之间的基础距离（增加此值让节点纵向更分散）

  const positions = new Map<string, { x: number; y: number }>();

  Array.from(groupedByLevel.entries())
    .sort(([a], [b]) => a - b)
    .forEach(([level, levelNodes]) => {
      // 优化排序：考虑连接关系
      const sorted = levelNodes.sort((a, b) => {
        // 优先按照前驱节点的平均位置排序
        const aParents = reverseAdjacency.get(a.id) ?? [];
        const bParents = reverseAdjacency.get(b.id) ?? [];
        
        if (aParents.length > 0 && bParents.length > 0) {
          const aAvgY = aParents.reduce((sum, parent) => {
            const pos = positions.get(parent);
            return sum + (pos?.y ?? 0);
          }, 0) / aParents.length;
          
          const bAvgY = bParents.reduce((sum, parent) => {
            const pos = positions.get(parent);
            return sum + (pos?.y ?? 0);
          }, 0) / bParents.length;
          
          return aAvgY - bAvgY;
        }
        
        // 回退到字母排序
        return a.label.localeCompare(b.label);
      });

      const count = sorted.length;
      // 动态调整行间距：节点越多，间距越大
      const rowSpacing = baseRowSpacing + Math.min(count * 10, 100);
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
  edges.map((edge) => {
    // Different colors based on dependency satisfaction status
    const edgeColor = edge.isSatisfied === false 
      ? 'rgba(248, 113, 113, 0.6)'  // Red for unsatisfied dependencies
      : edge.isSatisfied === true
        ? 'rgba(74, 222, 128, 0.6)'  // Green for satisfied dependencies
        : 'rgba(100, 181, 246, 0.6)'; // Blue for unknown status
    
    const markerColor = edge.isSatisfied === false 
      ? 'rgba(248, 113, 113, 0.8)'
      : edge.isSatisfied === true
        ? 'rgba(74, 222, 128, 0.8)'
        : 'rgba(100, 181, 246, 0.8)';

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'default', // 使用 default 类型，它会根据节点位置自动选择最佳路径
      animated: edge.isSatisfied === false, // Animate unsatisfied dependencies to draw attention
      style: {
        stroke: edgeColor,
        strokeWidth: 2.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: markerColor,
        width: 18,
        height: 18,
      },
      // 添加平滑的边缘半径
      pathOptions: {
        offset: 5,
        borderRadius: 20,
      },
    };
  });

const DagPreviewInner: React.FC<DagPreviewProps> = ({ nodes, edges, onSelectNode }) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState(buildNodes(nodes, edges));
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(buildEdges(edges));
  const { fitView } = useReactFlow();
  const initializedRef = useRef(false);

  useEffect(() => {
    setNodes(buildNodes(nodes, edges));
    setEdges(buildEdges(edges));
  }, [edges, nodes, setEdges, setNodes]);

  // 自定义左对齐的视图调整
  useEffect(() => {
    if (flowNodes.length > 0 && !initializedRef.current) {
      // 延迟执行以确保节点已渲染
      setTimeout(() => {
        // 首先使用 fitView 计算合适的缩放
        fitView({ 
          padding: 0.15,
          minZoom: 0.5,
          maxZoom: 1.5,
        });
        
        // 然后调整到左对齐位置
        setTimeout(() => {
          fitView({
            padding: 0.15,
            minZoom: 0.5,
            maxZoom: 1.5,
            nodes: flowNodes,
          });
        }, 50);
        
        initializedRef.current = true;
      }, 100);
    }
  }, [flowNodes, fitView]);

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView={false}
      defaultViewport={{ x: 50, y: 0, zoom: 0.65 }}
      onNodeClick={(_, node) => onSelectNode?.(node.id)}
      panOnScroll
      zoomOnScroll={true}
      nodesDraggable={false}
      nodesConnectable={false}
      edgesFocusable={false}
      elementsSelectable={true}
      proOptions={{ hideAttribution: true }}
      className="rounded-2xl border border-white/5 bg-black/40"
      style={{ height: '100%', minHeight: 260 }}
      defaultEdgeOptions={{
        type: 'default',
        animated: false,
        style: {
          strokeWidth: 2.5,
        },
      }}
    >
      <Controls showInteractive={false} position="bottom-left" />
      <Background gap={28} size={1.8} color="rgba(100, 116, 139, 0.2)" />
    </ReactFlow>
  );
};

const DagPreview: React.FC<DagPreviewProps> = (props) => (
  <ReactFlowProvider>
    <DagPreviewInner {...props} />
  </ReactFlowProvider>
);

export default DagPreview;
