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
  XCircle,
  Loader,
} from 'lucide-react';
import { Message } from '../../store/galaxyStore';
import { getWebSocketClient } from '../../services/websocket';

interface MessageBubbleProps {
  message: Message;
  nextMessage?: Message; // 用于检查下一条消息是否是 action
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
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-slate-200 shadow-glow">
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
  const status = action?.result?.status || action?.status;
  const resultError = action?.result?.error || action?.result?.message;
  const isContinue = status && String(status).toLowerCase() === 'continue';
  const operation = formatConstellationOperation(action);

  // 获取状态颜色
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
      {/* 连接线 */}
      <div className="absolute left-0 top-0 flex h-full w-6">
        <div className="w-px bg-white/10" />
        {!isLast && <div className="absolute left-0 top-7 h-[calc(100%-1.75rem)] w-px bg-white/10" />}
      </div>
      
      {/* Action 内容 */}
      <div className="ml-6 pb-3">
        <div className="flex items-start gap-2">
          {/* 横向连接线 */}
          <div className="mt-3 h-px w-3 flex-shrink-0 bg-white/10" />
          
          {/* Action 主内容 */}
          <div className="flex-1 min-w-0">
            <button
              onClick={onToggle}
              className="group flex w-full items-center gap-2 rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-left text-sm transition hover:border-white/20 hover:bg-white/10"
            >
              {/* 状态图标 */}
              <span className={clsx('flex-shrink-0', getStatusColor())}>
                {getStatusIcon(status)}
              </span>
              
              {/* 操作描述 */}
              <span className="flex-1 truncate font-medium text-slate-200">
                {operation}
              </span>
              
              {/* 展开/收起图标 */}
              {!isContinue && (action.arguments || resultError) && (
                <ChevronDown
                  className={clsx(
                    'h-3.5 w-3.5 flex-shrink-0 text-slate-400 transition-transform',
                    isExpanded && 'rotate-180'
                  )}
                />
              )}
            </button>

            {/* 展开的详细信息 */}
            {isExpanded && !isContinue && (
              <div className="mt-2 space-y-2 rounded-lg border border-white/5 bg-black/20 p-3">
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

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, nextMessage }) => {
  const [isExpanded, setExpanded] = useState(false);
  const [isThoughtExpanded, setThoughtExpanded] = useState(false);
  const [expandedActions, setExpandedActions] = useState<Set<number>>(new Set());
  const isUser = message.role === 'user';
  const isAction = message.kind === 'action';
  const responsePayload: PayloadRecord | undefined =
    message.kind === 'response' ? (message.payload as PayloadRecord | undefined) : undefined;
  const actionPayload: PayloadRecord | undefined =
    isAction ? (message.payload as PayloadRecord | undefined) : undefined;
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

  // 检查下一条消息是否是 action，如果是则附加到当前 response
  const hasAttachedActions = message.kind === 'response' && nextMessage?.kind === 'action';
  const attachedActionPayload = hasAttachedActions ? (nextMessage?.payload as PayloadRecord | undefined) : undefined;

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
          'max-w-[88%] rounded-3xl border px-6 py-5 shadow-xl backdrop-blur-lg sm:max-w-[74%]',
          isUser
            ? 'rounded-br-xl border-galaxy-blue/40 bg-gradient-to-br from-galaxy-blue/25 via-galaxy-purple/25 to-galaxy-blue/15 text-slate-50'
            : 'rounded-bl-xl border-white/10 bg-black/40 text-slate-200',
        )}
      >
        <div className="mb-3 flex items-center justify-between gap-3 text-xs text-slate-300">
          <span className="truncate font-semibold uppercase tracking-[0.24em] text-slate-200">
            {displayName}
          </span>
          <span>{timestamp}</span>
        </div>

        {!isUser && (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-[11px]">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 uppercase tracking-[0.18em] text-slate-200">
              <Sparkles className="h-3 w-3" aria-hidden />
              {message.kind}
            </span>
            {responseStatus && (
              <span className={clsx('inline-flex items-center gap-2 rounded-full px-3 py-1 uppercase tracking-[0.18em]', statusAccent(responseStatus))}>
                <CheckCircle2 className="h-3 w-3" aria-hidden />
                {String(responseStatus).toUpperCase()}
              </span>
            )}
            {actionPayload?.status && (
              <span className={clsx('inline-flex items-center gap-2 rounded-full px-3 py-1 uppercase tracking-[0.18em]', statusAccent(actionPayload.status))}>
                <CheckCircle2 className="h-3 w-3" aria-hidden />
                {String(actionPayload.status).toUpperCase()}
              </span>
            )}
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
            {responsePayload.results && responseStatus && String(responseStatus).toLowerCase() !== 'continue' && (
              <SectionCard title="Results" icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden />}>
                <pre className="whitespace-pre-wrap text-xs text-slate-200/90">
                  {JSON.stringify(responsePayload.results, null, 2)}
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
          </div>
        ) : message.kind === 'action' && actionPayload ? (
          // 独立的 action 消息 - 不显示，因为已经附加到 response 中
          null
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

      {/* 附加的 Actions 树形展示 */}
      {hasAttachedActions && attachedActionPayload && Array.isArray(attachedActionPayload.actions) && attachedActionPayload.actions.length > 0 && (
        <div className="ml-12 w-[calc(100%-3rem)] max-w-[calc(88%-3rem)] sm:max-w-[calc(74%-3rem)]">
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
