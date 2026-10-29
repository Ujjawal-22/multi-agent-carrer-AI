/**
 * Renders the actual LangGraph pipeline topology - not a decorative
 * illustration. Node positions and edges below match
 * backend/app/agents/orchestrator.py exactly:
 *
 *   START -> resume_analyzer --\
 *   START -> jd_analyzer -------> skill_gap -> ats_analysis ---------\
 *                                          \-> experience_analysis --> matching --> recommendation --------\
 *                                                                                \-> interview_prep --------> END
 *
 * Used as both the landing page hero (static, all nodes shown in their
 * "default" state) and the live analysis progress view (nodes fill in as
 * `completedNodeIds`/`activeNodeIds` are derived from real polled
 * current_step values - see hooks/useAnalysisPolling.ts). This is a
 * structural device that encodes real information, not decoration.
 */

export interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

const NODE_WIDTH = 132;
const NODE_HEIGHT = 40;

export const AGENT_NODES: GraphNode[] = [
  { id: "resume_analyzer", label: "Resume Analyzer", x: 16, y: 20 },
  { id: "jd_analyzer", label: "JD Analyzer", x: 16, y: 160 },
  { id: "skill_gap", label: "Skill Gap", x: 190, y: 90 },
  { id: "ats_analysis", label: "ATS Analysis", x: 364, y: 20 },
  { id: "experience_analysis", label: "Experience", x: 364, y: 160 },
  { id: "matching", label: "Matching", x: 538, y: 90 },
  { id: "recommendation", label: "Recommendation", x: 712, y: 20 },
  { id: "interview_prep", label: "Interview Prep", x: 712, y: 160 },
];

const EDGES: [string, string][] = [
  ["resume_analyzer", "skill_gap"],
  ["jd_analyzer", "skill_gap"],
  ["skill_gap", "ats_analysis"],
  ["skill_gap", "experience_analysis"],
  ["ats_analysis", "matching"],
  ["experience_analysis", "matching"],
  ["matching", "recommendation"],
  ["matching", "interview_prep"],
];

const nodeById = Object.fromEntries(AGENT_NODES.map((n) => [n.id, n]));

function edgePath(fromId: string, toId: string): string {
  const from = nodeById[fromId];
  const to = nodeById[toId];
  const startX = from.x + NODE_WIDTH;
  const startY = from.y + NODE_HEIGHT / 2;
  const endX = to.x;
  const endY = to.y + NODE_HEIGHT / 2;
  const midX = (startX + endX) / 2;
  return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
}

interface AgentGraphProps {
  completedNodeIds?: Set<string>;
  activeNodeIds?: Set<string>;
  className?: string;
}

export function AgentGraph({
  completedNodeIds = new Set(),
  activeNodeIds = new Set(),
  className,
}: AgentGraphProps) {
  return (
    <svg
      viewBox="0 0 864 220"
      className={className}
      role="img"
      aria-label="Multi-agent analysis pipeline diagram"
    >
      <g stroke="var(--color-line)" strokeWidth={1.5} fill="none">
        {EDGES.map(([from, to]) => (
          <path key={`${from}-${to}`} d={edgePath(from, to)} />
        ))}
      </g>

      {AGENT_NODES.map((node) => {
        const isCompleted = completedNodeIds.has(node.id);
        const isActive = activeNodeIds.has(node.id);

        return (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <rect
              width={NODE_WIDTH}
              height={NODE_HEIGHT}
              rx={4}
              fill={isCompleted ? "var(--color-signal-soft)" : "var(--color-paper-raised)"}
              stroke={isActive ? "var(--color-signal)" : "var(--color-line)"}
              strokeWidth={isActive ? 2 : 1}
            >
              {isActive && (
                <animate
                  attributeName="stroke-opacity"
                  values="1;0.35;1"
                  dur="1.6s"
                  repeatCount="indefinite"
                />
              )}
            </rect>
            <text
              x={NODE_WIDTH / 2}
              y={NODE_HEIGHT / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              fontFamily="var(--font-mono)"
              fontSize={11}
              fill="var(--color-ink)"
            >
              {node.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
