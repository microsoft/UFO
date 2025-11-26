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

const statusColors: Record<string, { bg: string; border: string; text: string; shadow: string; glow: string }> = {
  pending: {
    bg: 'linear-gradient(135deg, rgba(30,41,59,0.9) 0%, rgba(51,65,85,0.85) 100%)',
    border: 'rgba(148, 163, 184, 0.4)',
    text: '#cbd5e1',
    shadow: 'rgba(148, 163, 184, 0.5)',
    glow: '0 0 20px rgba(148, 163, 184, 0.3), 0 0 30px rgba(148, 163, 184, 0.15)',
  },
  running: {
    bg: 'linear-gradient(135deg, rgba(6,182,212,0.2) 0%, rgba(14,165,233,0.15) 50%, rgba(12,74,110,0.85) 100%)',
    border: 'rgba(56, 189, 248, 0.6)',
    text: '#bae6fd',
    shadow: 'rgba(56, 189, 248, 0.7)',
    glow: '0 0 25px rgba(56, 189, 248, 0.4), 0 0 35px rgba(6, 182, 212, 0.25), inset 0 0 20px rgba(56, 189, 248, 0.08)',
  },
  completed: {
    bg: 'linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(74,222,128,0.12) 50%, rgba(20,83,45,0.85) 100%)',
    border: 'rgba(74, 222, 128, 0.6)',
    text: '#bbf7d0',
    shadow: 'rgba(74, 222, 128, 0.7)',
    glow: '0 0 25px rgba(74, 222, 128, 0.4), 0 0 35px rgba(16, 185, 129, 0.25), inset 0 0 20px rgba(74, 222, 128, 0.08)',
  },
  failed: {
    bg: 'linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(248,113,113,0.12) 50%, rgba(127,29,29,0.85) 100%)',
    border: 'rgba(248, 113, 113, 0.6)',
    text: '#fecaca',
    shadow: 'rgba(248, 113, 113, 0.7)',
    glow: '0 0 25px rgba(248, 113, 113, 0.4), 0 0 35px rgba(239, 68, 68, 0.25), inset 0 0 20px rgba(248, 113, 113, 0.08)',
  },
  skipped: {
    bg: 'linear-gradient(135deg, rgba(250,204,21,0.2) 0%, rgba(253,224,71,0.12) 50%, rgba(113,63,18,0.85) 100%)',
    border: 'rgba(250, 204, 21, 0.6)',
    text: '#fef3c7',
    shadow: 'rgba(250, 204, 21, 0.7)',
    glow: '0 0 25px rgba(250, 204, 21, 0.4), 0 0 35px rgba(250, 204, 21, 0.25), inset 0 0 20px rgba(250, 204, 21, 0.08)',
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
          className="rounded-2xl border-2 px-5 py-4 text-left shadow-2xl backdrop-blur-sm transition-all duration-300 hover:scale-105"
          style={{
            background: colors.bg,
            borderColor: colors.border,
            boxShadow: `${colors.glow}, 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 2px rgba(255,255,255,0.1)`,
          }}
        >
          {/* Status icon badge in top-right corner with enhanced glow */}
          <div 
            className="absolute -top-2 -right-2 flex items-center justify-center rounded-full border-2 p-1.5 shadow-lg transition-all duration-300"
            style={{ 
              background: colors.bg,
              borderColor: colors.border,
              color: colors.text,
              boxShadow: `0 0 15px ${colors.shadow}, 0 0 8px ${colors.border}`,
            }}
          >
            {statusIcon}
          </div>
          
          {/* Inner glow accent line at top */}
          <div 
            className="absolute top-0 left-0 right-0 h-[1px] opacity-50"
            style={{ 
              background: `linear-gradient(90deg, transparent 0%, ${colors.border} 50%, transparent 100%)`,
            }}
          />
          
          <div 
            className="text-xl font-semibold uppercase tracking-wider mb-2 drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]"
            style={{ color: colors.text, opacity: 0.85 }}
          >
            {data.taskId}
          </div>
          <div 
            className="text-2xl font-bold leading-snug drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)]"
            style={{ color: colors.text }}
          >
            {data.label}
          </div>
          
          {/* Bottom accent line */}
          <div 
            className="absolute bottom-0 left-0 right-0 h-[1px] opacity-30"
            style={{ 
              background: `linear-gradient(90deg, transparent 0%, ${colors.border} 50%, transparent 100%)`,
            }}
          />
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

  // Use topological sort to calculate levels
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

  // Ensure all nodes have levels
  nodes.forEach((node) => {
    if (!levels.has(node.id)) {
      levels.set(node.id, 0);
    }
  });

  // Group by level
  const groupedByLevel = new Map<number, DagNode[]>();
  nodes.forEach((node) => {
    const level = levels.get(node.id) ?? 0;
    if (!groupedByLevel.has(level)) {
      groupedByLevel.set(level, []);
    }
    groupedByLevel.get(level)!.push(node);
  });

  // Increase spacing to reduce crowding and line crossings
  const columnSpacing = 500;  // Horizontal spacing: distance between levels (increased for better separation)
  const baseRowSpacing = 200; // Vertical spacing: basic distance between nodes in the same level (increased for less overlap)
  const leftMargin = -100;    // Negative margin to shift entire graph left and center it better

  const positions = new Map<string, { x: number; y: number }>();

  Array.from(groupedByLevel.entries())
    .sort(([a], [b]) => a - b)
    .forEach(([level, levelNodes]) => {
      // Enhanced sorting: consider connection relationships more carefully
      const sorted = levelNodes.sort((a, b) => {
        const aParents = reverseAdjacency.get(a.id) ?? [];
        const bParents = reverseAdjacency.get(b.id) ?? [];
        
        // If both nodes have parents, sort by parent average position
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
        
        // If only one has parents, prioritize that one's position
        if (aParents.length > 0) {
          const aAvgY = aParents.reduce((sum, parent) => {
            const pos = positions.get(parent);
            return sum + (pos?.y ?? 0);
          }, 0) / aParents.length;
          return aAvgY;
        }
        
        if (bParents.length > 0) {
          const bAvgY = bParents.reduce((sum, parent) => {
            const pos = positions.get(parent);
            return sum + (pos?.y ?? 0);
          }, 0) / bParents.length;
          return -bAvgY;
        }
        
        // Fallback to alphabetical sorting
        return a.label.localeCompare(b.label);
      });

      const count = sorted.length;
      const rowSpacing = baseRowSpacing + Math.min(count * 15, 150);
      
      if (level === 0) {
        // First level - evenly distribute vertically
        const totalHeight = (count - 1) * rowSpacing;
        const startY = totalHeight > 0 ? -(totalHeight / 2) : 0;
        
        sorted.forEach((node, index) => {
          positions.set(node.id, {
            x: leftMargin + level * columnSpacing,
            y: startY + index * rowSpacing,
          });
        });
      } else {
        // For subsequent levels, distribute nodes while avoiding overlaps
        // Group nodes by their parent center position
        const nodesByParentCenter = new Map<number, DagNode[]>();
        
        sorted.forEach((node) => {
          const parents = reverseAdjacency.get(node.id) ?? [];
          const avgY = parents.length > 0
            ? parents.reduce((sum, parent) => {
                const pos = positions.get(parent);
                return sum + (pos?.y ?? 0);
              }, 0) / parents.length
            : 0;
          
          // Round to avoid floating point issues
          const key = Math.round(avgY / 10) * 10;
          if (!nodesByParentCenter.has(key)) {
            nodesByParentCenter.set(key, []);
          }
          nodesByParentCenter.get(key)!.push(node);
        });
        
        // Now position each group of nodes
        nodesByParentCenter.forEach((nodesGroup, centerY) => {
          const groupCount = nodesGroup.length;
          if (groupCount === 1) {
            // Single node - place at parent center
            positions.set(nodesGroup[0].id, {
              x: leftMargin + level * columnSpacing,
              y: centerY,
            });
          } else {
            // Multiple nodes - distribute them around parent center
            const groupHeight = (groupCount - 1) * rowSpacing;
            const startY = centerY - groupHeight / 2;
            
            nodesGroup.forEach((node, index) => {
              positions.set(node.id, {
                x: leftMargin + level * columnSpacing,
                y: startY + index * rowSpacing,
              });
            });
          }
        });
      }
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
    // Enhanced colors with glow effect based on dependency satisfaction status
    const edgeConfig = edge.isSatisfied === false 
      ? { 
          color: 'rgba(248, 113, 113, 0.8)',
          gradient: 'linear-gradient(to right, rgba(248, 113, 113, 0.9), rgba(239, 68, 68, 0.7))',
          glowColor: 'rgba(239, 68, 68, 0.6)',
          markerColor: 'rgba(248, 113, 113, 1)',
          pulseColor: '#ef4444',
        } // Red for unsatisfied dependencies
      : edge.isSatisfied === true
        ? { 
            color: 'rgba(74, 222, 128, 0.8)',
            gradient: 'linear-gradient(to right, rgba(74, 222, 128, 0.9), rgba(16, 185, 129, 0.7))',
            glowColor: 'rgba(16, 185, 129, 0.6)',
            markerColor: 'rgba(74, 222, 128, 1)',
            pulseColor: '#10b981',
          } // Green for satisfied dependencies
        : { 
            color: 'rgba(56, 189, 248, 0.8)',
            gradient: 'linear-gradient(to right, rgba(56, 189, 248, 0.9), rgba(6, 182, 212, 0.7))',
            glowColor: 'rgba(6, 182, 212, 0.6)',
            markerColor: 'rgba(56, 189, 248, 1)',
            pulseColor: '#06b6d4',
          }; // Cyan for unknown status

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'default', // Use default bezier for smoother curves
      animated: true, // Always animate for futuristic effect
      className: `futuristic-edge ${edge.isSatisfied === false ? 'edge-unsatisfied' : edge.isSatisfied === true ? 'edge-satisfied' : 'edge-default'}`,
      style: {
        stroke: edgeConfig.color,
        strokeWidth: 3,
        filter: `drop-shadow(0 0 4px ${edgeConfig.glowColor}) drop-shadow(0 0 8px ${edgeConfig.glowColor})`,
      },
      markerEnd: {
        type: MarkerType.Arrow,
        color: edgeConfig.markerColor,
        width: 22,
        height: 22,
        strokeWidth: 2.5,
      },
      data: {
        pulseColor: edgeConfig.pulseColor,
      },
    };
  });

const DagPreviewInner: React.FC<DagPreviewProps> = ({ nodes, edges, onSelectNode }) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState(buildNodes(nodes, edges));
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(buildEdges(edges));
  const { setViewport } = useReactFlow();
  const initializedRef = useRef(false);

  useEffect(() => {
    setNodes(buildNodes(nodes, edges));
    setEdges(buildEdges(edges));
  }, [edges, nodes, setEdges, setNodes]);

  // Custom viewport adjustment - left-aligned view
  useEffect(() => {
    if (flowNodes.length > 0 && !initializedRef.current) {
      setTimeout(() => {
        // Calculate bounds manually for left-aligned layout
        const minX = Math.min(...flowNodes.map(node => node.position.x));
        const maxX = Math.max(...flowNodes.map(node => node.position.x));
        const minY = Math.min(...flowNodes.map(node => node.position.y));
        const maxY = Math.max(...flowNodes.map(node => node.position.y));
        
        const width = maxX - minX + 280; // 280 is node width
        const height = maxY - minY + 180; // 180 is node height
        
        // Get container dimensions
        const container = document.querySelector('.react-flow');
        const containerWidth = container?.clientWidth || 800;
        const containerHeight = container?.clientHeight || 600;
        
        // Calculate zoom to fit vertically with some padding
        const zoomX = (containerWidth * 0.95) / width; // Use 95% of width
        const zoomY = (containerHeight * 0.90) / height; // Use 90% of height
        const zoom = Math.max(Math.min(zoomX, zoomY, 1.5), 0.45); // Take smaller zoom to fit, min 0.7, cap at 1.5x
        
        // Left-align: small left padding (50px in zoomed space)
        const x = -minX * zoom + 30;
        // Center vertically
        const y = (containerHeight - height * zoom) / 2 - minY * zoom;
        
        setViewport({ x, y, zoom });
        initializedRef.current = true;
      }, 150);
    }
  }, [flowNodes, setViewport]);

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView={false}
      defaultViewport={{ x: -50, y: 0, zoom: 0.6 }}
      minZoom={0.1}
      maxZoom={2}
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
