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
} from 'lucide-react';
import { Message } from '../../store/galaxyStore';
import { getWebSocketClient } from '../../services/websocket';

interface MessageBubbleProps {
  message: Message;
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
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/10 text-slate-100 shadow-glow">
          {icon}
        </span>
        {title}
      </div>
      <div className="space-y-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
        {children}
      </div>
    </div>
  );

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [isExpanded, setExpanded] = useState(false);
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
            : 'rounded-bl-xl border-white/10 bg-black/35 text-slate-100',
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
                <p>{responsePayload.thought}</p>
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
            {responsePayload.results && (
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
              <div className="prose prose-invert max-w-none text-sm leading-relaxed prose-headings:text-slate-50 prose-p:mb-3 prose-pre:bg-slate-900/80 prose-strong:text-white">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            )}
          </div>
        ) : message.kind === 'action' && actionPayload ? (
          <div className="space-y-3">
            {Array.isArray(actionPayload.actions) ? (
              actionPayload.actions.map((action: any, index: number) => {
                const status = action?.result?.status || action?.status;
                const statusClass = statusAccent(status);
                const resultError = action?.result?.error || action?.result?.message;
                return (
                  <div key={index} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs uppercase tracking-[0.18em] text-slate-300">
                      <span className="flex items-center gap-2 text-slate-200">
                        <Command className="h-3.5 w-3.5" aria-hidden />
                        {action.function || action.action || action.command || `Action ${index + 1}`}
                      </span>
                      {status && <span className={clsx('inline-flex items-center gap-2 rounded-full px-3 py-1', statusClass)}>{String(status).toUpperCase()}</span>}
                    </div>
                    {action.arguments && (
                      <pre className="whitespace-pre-wrap text-xs text-slate-200/90">
                        {JSON.stringify(action.arguments, null, 2)}
                      </pre>
                    )}
                    {resultError && (
                      <div className="mt-2 rounded-xl border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
                        {String(resultError)}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <SectionCard title="Action" icon={<Command className="h-3.5 w-3.5" aria-hidden />}>
                <pre className="whitespace-pre-wrap text-xs text-slate-200/90">
                  {JSON.stringify(actionPayload, null, 2)}
                </pre>
              </SectionCard>
            )}
          </div>
        ) : (
          <div className="prose prose-invert max-w-none text-sm leading-relaxed prose-headings:text-slate-50 prose-p:mb-3 prose-pre:bg-slate-900/80 prose-strong:text-white">
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
    </div>
  );
};

export default MessageBubble;
