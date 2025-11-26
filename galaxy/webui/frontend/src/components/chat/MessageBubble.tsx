import React, { ReactNode, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Command,
  ListTree,
  RefreshCcw,
  Rocket,
  Sparkles,
  User,
  XCircle,
  Loader,
  Zap,
} from 'lucide-react';
import { Message } from '../../store/galaxyStore';
import { getWebSocketClient } from '../../services/websocket';

interface MessageBubbleProps {
  message: Message;
  nextMessage?: Message; // Used to check if the next message is an action
  stepNumber?: number; // Step number
}

type PayloadRecord = Record<string, any>;

const formatTimestamp = (timestamp: number) => {
  try {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(timestamp);
  } catch (error) {
    return '';
  }
};

const statusAccent = (status?: string) => {
  if (!status) return 'bg-slate-500/30 text-slate-200 border border-white/10';
  const normalized = status.toLowerCase();
  if (['finish', 'completed', 'success', 'ready'].some((key) => normalized.includes(key))) {
    return 'bg-emerald-500/20 text-emerald-200 border border-emerald-400/30';
  }
  if (['fail', 'error'].some((key) => normalized.includes(key))) {
    return 'bg-rose-500/20 text-rose-200 border border-rose-400/30';
  }
  if (['continue', 'running', 'in_progress'].some((key) => normalized.includes(key))) {
    return 'bg-amber-500/20 text-amber-100 border border-amber-400/30';
  }
  return 'bg-slate-500/30 text-slate-200 border border-white/10';
};

const SectionCard: React.FC<{ title: string; icon: ReactNode; children: ReactNode }> = ({ title, icon, children }) => (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-200">
      <div className="mb-2 flex items-center gap-2 text-[12px] uppercase tracking-[0.18em] text-slate-400">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-slate-200 shadow-[0_0_12px_rgba(33,240,255,0.25)]">
          {icon}
        </span>
        {title}
      </div>
      <div className="space-y-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
        {children}
      </div>
    </div>
  );

/**
 * Format constellation operation into human-readable text.
 * Mirrors the backend's _format_constellation_operation logic.
 */
const formatConstellationOperation = (action: any): string => {
  const func = action?.function;
  const args = action?.arguments || {};

  if (!func) {
    return action?.action || action?.command || 'Unknown Action';
  }

  // Format different types of operations
  switch (func) {
    case 'add_task': {
      const taskId = args.task_id || '?';
      const name = args.name || '';
      return name ? `Add Task: '${taskId}' (${name})` : `Add Task: '${taskId}'`;
    }

    case 'remove_task': {
      const taskId = args.task_id || '?';
      return `Remove Task: '${taskId}'`;
    }

    case 'update_task': {
      const taskId = args.task_id || '?';
      // Show which fields are being updated
      const updateFields = Object.keys(args).filter(
        (k) => k !== 'task_id' && args[k] !== null && args[k] !== undefined
      );
      const fieldsStr = updateFields.length > 0 ? updateFields.join(', ') : 'fields';
      return `Update Task: '${taskId}' (${fieldsStr})`;
    }

    case 'add_dependency': {
      const depId = args.dependency_id || '?';
      const fromTask = args.from_task_id || '?';
      const toTask = args.to_task_id || '?';
      return `Add Dependency (ID ${depId}): ${fromTask} → ${toTask}`;
    }

    case 'remove_dependency': {
      const depId = args.dependency_id || '?';
      return `Remove Dependency: '${depId}'`;
    }

    case 'update_dependency': {
      const depId = args.dependency_id || '?';
      return `Update Dependency: '${depId}'`;
    }

    case 'build_constellation': {
      const config = args.config || {};
      
      // First check if there is a simplified format (task_count and dependency_count)
      if (args.task_count !== undefined || args.dependency_count !== undefined) {
        const taskCount = args.task_count || 0;
        const depCount = args.dependency_count || 0;
        return `Build Constellation (${taskCount} tasks, ${depCount} dependencies)`;
      }
      
      // Fallback to full config format
      if (typeof config === 'object' && config !== null) {
        const taskCount = Array.isArray(config.tasks) ? config.tasks.length : 0;
        const depCount = Array.isArray(config.dependencies) ? config.dependencies.length : 0;
        return `Build Constellation (${taskCount} tasks, ${depCount} dependencies)`;
      }
      
      return 'Build Constellation';
    }

    case 'clear_constellation':
      return 'Clear Constellation (remove all tasks)';

    case 'load_constellation': {
      const filePath = args.file_path || '?';
      // Extract filename from path
      const filename = filePath.split(/[/\\]/).pop() || filePath;
      return `Load Constellation from '${filename}'`;
    }

    case 'save_constellation': {
      const filePath = args.file_path || '?';
      // Extract filename from path
      const filename = filePath.split(/[/\\]/).pop() || filePath;
      return `Save Constellation to '${filename}'`;
    }

    default: {
      // Fallback for unknown operations - show function name with first 2 arguments
      const argEntries = Object.entries(args).slice(0, 2);
      if (argEntries.length > 0) {
        const argsStr = argEntries.map(([k, v]) => `${k}=${v}`).join(', ');
        return `${func}(${argsStr})`;
      }
      return func;
    }
  }
};

/**
 * Get status icon for action result
 */
const getStatusIcon = (status?: string) => {
  if (!status) return <Loader className="h-3.5 w-3.5" />;
  const normalized = status.toLowerCase();
  if (['finish', 'completed', 'success', 'ready'].some((key) => normalized.includes(key))) {
    return <CheckCircle2 className="h-3.5 w-3.5" />;
  }
  if (['fail', 'error'].some((key) => normalized.includes(key))) {
    return <XCircle className="h-3.5 w-3.5" />;
  }
  if (['continue', 'running', 'in_progress'].some((key) => normalized.includes(key))) {
    return <Loader className="h-3.5 w-3.5" />;
  }
  return <Loader className="h-3.5 w-3.5" />;
};

/**
 * Render action as a tree node attached to response
 */
const ActionTreeNode: React.FC<{
  action: any;
  index: number;
  isLast: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ action, isLast, isExpanded, onToggle }) => {
  // Get status: prioritize from result.status, then status, then arguments.status
  const status = action?.result?.status || action?.status || action?.arguments?.status;
  const resultError = action?.result?.error || action?.result?.message;
  const isContinue = status && String(status).toLowerCase() === 'continue';
  const operation = formatConstellationOperation(action);

  // Get status color
  const getStatusColor = () => {
    if (!status) return 'text-slate-400';
    const normalized = status.toLowerCase();
    if (['finish', 'completed', 'success', 'ready'].some((key) => normalized.includes(key))) {
      return 'text-emerald-400';
    }
    if (['fail', 'error'].some((key) => normalized.includes(key))) {
      return 'text-rose-400';
    }
    if (['continue', 'running', 'in_progress'].some((key) => normalized.includes(key))) {
      return 'text-amber-400';
    }
    return 'text-slate-400';
  };

  return (
    <div className="relative">
      {/* Vertical connecting line */}
      <div className="absolute left-0 top-0 flex h-full w-6">
        <div className="w-px bg-white/10" />
        {!isLast && <div className="absolute left-0 top-7 h-[calc(100%-1.75rem)] w-px bg-white/10" />}
      </div>
      
      {/* Action content */}
      <div className="ml-6 pb-3">
        <div className="flex items-start gap-2">
          {/* Horizontal connecting line */}
          <div className="mt-3 h-px w-3 flex-shrink-0 bg-white/10" />
          
          {/* Action main content */}
          <div className="flex-1 min-w-0">
            <button
              onClick={onToggle}
              className="group flex w-full items-center gap-2 rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-left text-sm transition hover:border-white/20 hover:bg-white/10"
            >
              {/* Status icon */}
              <span className={clsx('flex-shrink-0', getStatusColor())}>
                {getStatusIcon(status)}
              </span>
              
              {/* Operation description */}
              <span className="flex-1 truncate font-medium text-slate-200">
                {operation}
              </span>
              
              {/* Expand/collapse icon */}
              {!isContinue && (action.arguments || resultError) && (
                <ChevronDown
                  className={clsx(
                    'h-3.5 w-3.5 flex-shrink-0 text-slate-400 transition-transform',
                    isExpanded && 'rotate-180'
                  )}
                />
              )}
            </button>

            {/* Expanded details */}
            {isExpanded && !isContinue && (
              <div className="mt-2 space-y-2 rounded-lg border border-white/5 bg-black/20 p-3">
                {/* Status display */}
                {status && (
                  <div>
                    <div className="mb-1 text-[10px] uppercase tracking-wider text-slate-400">
                      Status
                    </div>
                    <div className={clsx('text-sm font-medium', getStatusColor())}>
                      {String(status).toUpperCase()}
                    </div>
                  </div>
                )}
                {action.arguments && (
                  <div>
                    <div className="mb-1 text-[10px] uppercase tracking-wider text-slate-400">
                      Arguments
                    </div>
                    <pre className="whitespace-pre-wrap rounded-lg border border-white/5 bg-black/30 p-2 text-xs text-slate-300">
                      {JSON.stringify(action.arguments, null, 2)}
                    </pre>
                  </div>
                )}
                {/* Debug: Show full action object */}
                <div>
                  <div className="mb-1 text-[10px] uppercase tracking-wider text-slate-400">
                    Full Action Object (Debug)
                  </div>
                  <pre className="whitespace-pre-wrap rounded-lg border border-white/5 bg-black/30 p-2 text-xs text-slate-300">
                    {JSON.stringify(action, null, 2)}
                  </pre>
                </div>
                {resultError && (
                  <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 p-2">
                    <div className="mb-1 text-[10px] uppercase tracking-wider text-rose-300">
                      Error
                    </div>
                    <div className="text-xs text-rose-100">{String(resultError)}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, nextMessage, stepNumber }) => {
  const [isExpanded, setExpanded] = useState(false);
  const [isThoughtExpanded, setThoughtExpanded] = useState(false);
  const [expandedActions, setExpandedActions] = useState<Set<number>>(new Set());
  const isUser = message.role === 'user';
  const isAction = message.kind === 'action';
  const responsePayload: PayloadRecord | undefined =
    message.kind === 'response' ? (message.payload as PayloadRecord | undefined) : undefined;
  const showPayloadToggle = Boolean(message.payload) && (isAction || message.kind === 'system');

  const timestamp = useMemo(() => formatTimestamp(message.timestamp), [message.timestamp]);
  const displayName = useMemo(() => {
    if (isUser) {
      return 'You';
    }
    if (!message.agentName) {
      return 'UFO';
    }
    return message.agentName.toLowerCase().includes('constellation') ? 'UFO' : message.agentName;
  }, [isUser, message.agentName]);

  const responseStatus = responsePayload?.status;

  // Check if next message is an action, if so attach it to current response
  const hasAttachedActions = message.kind === 'response' && nextMessage?.kind === 'action';
  const attachedActionPayload = hasAttachedActions ? (nextMessage?.payload as PayloadRecord | undefined) : undefined;

  // If it is an action message, return null directly without rendering any content (because it has been attached to response)
  if (isAction) {
    return null;
  }

  const handleReplay = () => {
    if (!message.payload) {
      return;
    }
    getWebSocketClient().send({
      type: 'replay_action',
      timestamp: Date.now(),
      payload: message.payload,
    });
  };

  return (
    <div
      className={clsx('flex w-full flex-col gap-2 transition-all', {
        'items-end': isUser,
        'items-start': !isUser,
      })}
    >
      <div
        className={clsx(
          'w-[88%] rounded-3xl border px-6 py-5 shadow-xl sm:w-[74%]',
          isUser
            ? 'rounded-br-xl border-galaxy-blue/50 bg-gradient-to-br from-galaxy-blue/25 via-galaxy-purple/25 to-galaxy-blue/15 text-slate-50 shadow-[0_0_30px_rgba(15,123,255,0.2),inset_0_1px_0_rgba(147,197,253,0.15)]'
            : 'rounded-bl-xl border-[rgba(10,186,181,0.35)] bg-gradient-to-br from-[rgba(10,186,181,0.12)] via-[rgba(12,50,65,0.8)] to-[rgba(11,30,45,0.85)] text-slate-100 shadow-[0_0_25px_rgba(10,186,181,0.18),inset_0_1px_0_rgba(10,186,181,0.12)]',
        )}
      >
        {/* Agent message header */}
        {!isUser && (
          <div className="mb-4 flex items-center justify-between gap-3">
            {/* Left side: Agent name and icon */}
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-400/30 shadow-lg">
                <Zap className="h-5 w-5 text-cyan-300" aria-hidden />
              </div>
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-base text-slate-100">
                    {displayName}
                  </span>
                  {stepNumber !== undefined && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-300">
                      <span className="opacity-70">STEP</span>
                      <span>{stepNumber}</span>
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-slate-400">{timestamp}</span>
              </div>
            </div>

            {/* Right side: Status label */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-slate-300">
                <Sparkles className="h-3 w-3" aria-hidden />
                {message.kind}
              </span>
              {responseStatus && (
                <span className={clsx('inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider', statusAccent(responseStatus))}>
                  <CheckCircle2 className="h-3 w-3" aria-hidden />
                  {String(responseStatus).toUpperCase()}
                </span>
              )}
            </div>
          </div>
        )}

        {/* User message header */}
        {isUser && (
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-400/30 shadow-lg">
                <User className="h-5 w-5 text-purple-300" aria-hidden />
              </div>
              <div className="flex flex-col gap-0.5">
                <span className="font-bold text-base text-slate-100">
                  {displayName}
                </span>
                <span className="text-[10px] text-slate-400">{timestamp}</span>
              </div>
            </div>
          </div>
        )}

        {message.kind === 'response' && responsePayload ? (
          <div className="space-y-4">
            {responsePayload.thought && (
              <SectionCard title="Thought" icon={<Brain className="h-3.5 w-3.5" aria-hidden />}>
                {(() => {
                  const thought = String(responsePayload.thought);
                  const maxLength = 100;
                  const isTooLong = thought.length > maxLength;
                  
                  if (!isTooLong) {
                    return <p>{thought}</p>;
                  }

                  // Find a good break point
                  let truncateAt = maxLength;
                  const breakChars = ['. ', '.\n', '! ', '!\n', '? ', '?\n'];
                  for (const breakChar of breakChars) {
                    const idx = thought.lastIndexOf(breakChar, maxLength);
                    if (idx > maxLength * 0.7) {
                      truncateAt = idx + breakChar.length;
                      break;
                    }
                  }

                  return (
                    <div>
                      <p>
                        {isThoughtExpanded ? thought : thought.substring(0, truncateAt).trim() + '...'}
                      </p>
                      <button
                        onClick={() => setThoughtExpanded(!isThoughtExpanded)}
                        className="mt-2 inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300 transition hover:border-white/30 hover:bg-white/10"
                      >
                        {isThoughtExpanded ? (
                          <>
                            <ChevronUp className="h-3 w-3" aria-hidden />
                            Show less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3 w-3" aria-hidden />
                            Show more ({thought.length} chars)
                          </>
                        )}
                      </button>
                    </div>
                  );
                })()}
              </SectionCard>
            )}
            {responsePayload.plan && (
              <SectionCard title="Plan" icon={<ListTree className="h-3.5 w-3.5" aria-hidden />}>
                {Array.isArray(responsePayload.plan) ? (
                  <ul className="space-y-1 text-sm">
                    {responsePayload.plan.map((step: string, index: number) => (
                      <li key={index} className="flex items-start gap-2 text-slate-200">
                        <span className="mt-[2px] h-2 w-2 rounded-full bg-galaxy-blue" aria-hidden />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>{responsePayload.plan}</p>
                )}
              </SectionCard>
            )}
            {responsePayload.decomposition_strategy && (
              <SectionCard title="Decomposition" icon={<Command className="h-3.5 w-3.5" aria-hidden />}>
                <p>{responsePayload.decomposition_strategy}</p>
              </SectionCard>
            )}
            {responsePayload.ask_details && (
              <SectionCard title="Ask Details" icon={<Rocket className="h-3.5 w-3.5" aria-hidden />}>
                <pre className="whitespace-pre-wrap text-xs text-slate-200/90">
                  {JSON.stringify(responsePayload.ask_details, null, 2)}
                </pre>
              </SectionCard>
            )}
            {responsePayload.actions_summary && (
              <SectionCard title="Action Summary" icon={<Sparkles className="h-3.5 w-3.5" aria-hidden />}>
                <p>{responsePayload.actions_summary}</p>
              </SectionCard>
            )}
            {(responsePayload.response || responsePayload.final_response) && (
              <SectionCard title="Response" icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden />}>
                <p>{responsePayload.final_response || responsePayload.response}</p>
              </SectionCard>
            )}
            {responsePayload.validation && (
              <SectionCard title="Validation" icon={<AlertTriangle className="h-3.5 w-3.5" aria-hidden />}>
                <pre className="whitespace-pre-wrap text-xs text-slate-200/90">
                  {JSON.stringify(responsePayload.validation, null, 2)}
                </pre>
              </SectionCard>
            )}
            {!(
              responsePayload.thought ||
              responsePayload.plan ||
              responsePayload.actions_summary ||
              responsePayload.response ||
              responsePayload.final_response
            ) && (
              <div className="prose prose-invert max-w-none text-sm leading-relaxed prose-headings:text-slate-100 prose-p:mb-3 prose-p:text-slate-200 prose-pre:bg-slate-900/80 prose-strong:text-slate-100">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            )}
            
            {/* Final Results - Prominently displayed at the end */}
            {responsePayload.results && responseStatus && String(responseStatus).toLowerCase() !== 'continue' && (
              <div className={clsx(
                'mt-6 rounded-2xl border-2 p-6 shadow-xl',
                String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                  ? 'border-rose-500/50 bg-gradient-to-br from-rose-500/15 to-rose-600/8'
                  : 'border-emerald-500/50 bg-gradient-to-br from-emerald-500/15 to-emerald-600/8'
              )}>
                <div className="mb-4 flex items-center gap-3">
                  <div className={clsx(
                    'flex h-10 w-10 items-center justify-center rounded-xl shadow-lg',
                    String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                      ? 'bg-gradient-to-br from-rose-500/35 to-rose-600/25 border border-rose-400/40'
                      : 'bg-gradient-to-br from-emerald-500/35 to-emerald-600/25 border border-emerald-400/40'
                  )}>
                    {String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error') ? (
                      <XCircle className="h-5 w-5 text-rose-300" aria-hidden />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-emerald-300" aria-hidden />
                    )}
                  </div>
                  <div>
                    <h3 className={clsx(
                      'text-base font-bold uppercase tracking-wider',
                      String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                        ? 'text-rose-200'
                        : 'text-emerald-200'
                    )}>
                      Final Results
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Status: {String(responseStatus).toUpperCase()}
                    </p>
                  </div>
                </div>
                <div className={clsx(
                  'rounded-xl border p-4',
                  String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                    ? 'border-rose-400/20 bg-rose-950/30'
                    : 'border-emerald-400/20 bg-emerald-950/30'
                )}>
                  {typeof responsePayload.results === 'string' ? (
                    <div className={clsx(
                      'whitespace-pre-wrap text-sm leading-relaxed',
                      String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                        ? 'text-rose-100/90'
                        : 'text-emerald-100/90'
                    )}>
                      {responsePayload.results}
                    </div>
                  ) : (
                    <pre className={clsx(
                      'whitespace-pre-wrap text-sm leading-relaxed',
                      String(responseStatus).toLowerCase().includes('fail') || String(responseStatus).toLowerCase().includes('error')
                        ? 'text-rose-100/90'
                        : 'text-emerald-100/90'
                    )}>
                      {JSON.stringify(responsePayload.results, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="prose prose-invert max-w-none text-sm leading-relaxed prose-headings:text-slate-100 prose-p:mb-3 prose-p:text-slate-200 prose-pre:bg-slate-900/80 prose-strong:text-slate-100">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}

        {(showPayloadToggle || isAction) && (
          <div className="mt-5 flex items-center gap-3 text-xs text-slate-300">
            {isAction && (
              <button
                type="button"
                onClick={handleReplay}
                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 transition hover:border-white/30 hover:bg-white/10"
              >
                <RefreshCcw className="h-3 w-3" aria-hidden />
                Replay
              </button>
            )}
            {showPayloadToggle && (
              <button
                type="button"
                onClick={() => setExpanded((value) => !value)}
                className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 transition hover:border-white/30 hover:bg-white/10"
              >
                {isExpanded ? 'Hide JSON' : 'View JSON'}
                {isExpanded ? (
                  <ChevronUp className="h-3 w-3" aria-hidden />
                ) : (
                  <ChevronDown className="h-3 w-3" aria-hidden />
                )}
              </button>
            )}
          </div>
        )}

        <AnimatePresence initial={false}>
          {showPayloadToggle && isExpanded && (
            <motion.pre
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-3 max-h-80 overflow-auto rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-cyan-100"
            >
              {JSON.stringify(message.payload, null, 2)}
            </motion.pre>
          )}
        </AnimatePresence>
      </div>

      {/* Attached Actions tree view */}
      {hasAttachedActions && attachedActionPayload && Array.isArray(attachedActionPayload.actions) && attachedActionPayload.actions.length > 0 && (
        <div className="ml-12 w-[calc(88%-3rem)] sm:w-[calc(74%-3rem)]">
          {attachedActionPayload.actions.map((action: any, index: number) => (
            <ActionTreeNode
              key={index}
              action={action}
              index={index}
              isLast={index === attachedActionPayload.actions.length - 1}
              isExpanded={expandedActions.has(index)}
              onToggle={() => {
                const newExpanded = new Set(expandedActions);
                if (newExpanded.has(index)) {
                  newExpanded.delete(index);
                } else {
                  newExpanded.add(index);
                }
                setExpandedActions(newExpanded);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
