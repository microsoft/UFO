import React, { useEffect, useMemo, useRef } from 'react';
import { shallow } from 'zustand/shallow';
import { Loader2 } from 'lucide-react';
import SearchFilterBar from '../common/SearchFilterBar';
import MessageBubble from './MessageBubble';
import Composer from './Composer';
import { Message, useGalaxyStore } from '../../store/galaxyStore';

const filterMessages = (messages: Message[], query: string, kind: string) => {
  const normalizedQuery = query.toLowerCase().trim();
  return messages.filter((message) => {
    const matchesKind = kind === 'all' || message.kind === kind;
    if (!matchesKind) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    const haystack = [message.content, message.agentName, message.role]
      .filter(Boolean)
      .map((value) => String(value).toLowerCase())
      .join(' ');
    return haystack.includes(normalizedQuery);
  });
};

const ChatWindow: React.FC = () => {
  const { messages, searchQuery, messageKind, isTaskStopped } = useGalaxyStore(
    (state) => ({
      messages: state.messages,
      searchQuery: state.ui.searchQuery,
      messageKind: state.ui.messageKindFilter,
      isTaskStopped: state.ui.isTaskStopped,
    }),
    shallow,
  );

  const listRef = useRef<HTMLDivElement>(null);

  const filteredMessages = useMemo(
    () => filterMessages(messages, searchQuery, messageKind),
    [messages, messageKind, searchQuery],
  );

  // Calculate step numbers for agent messages (excluding user and action messages)
  // Step counter resets after each user message
  const messageSteps = useMemo(() => {
    const steps = new Map<string, number>();
    let stepCounter = 0;
    
    filteredMessages.forEach((message) => {
      // Reset counter when encountering a user message
      if (message.role === 'user') {
        stepCounter = 0;
      } 
      // Only count non-user, non-action messages for step numbering
      else if (message.kind !== 'action') {
        stepCounter++;
        steps.set(message.id, stepCounter);
      }
    });
    
    return steps;
  }, [filteredMessages]);

  // Check if we're waiting for agent response (based on ALL messages, not filtered)
  const isWaitingForResponse = useMemo(() => {
    if (messages.length === 0) return false;
    
    const lastMessage = messages[messages.length - 1];
    
    // If last message is from user, we're waiting for response
    if (lastMessage.role === 'user') {
      return true;
    }
    
    // If last message is agent but it's an action (not final response), we're still waiting
    if (lastMessage.role === 'assistant' && lastMessage.kind === 'action') {
      return true;
    }
    
    // If last message is agent response but status is pending/running/continue, still waiting
    if (lastMessage.role === 'assistant' && lastMessage.kind === 'response') {
      const status = String(lastMessage.payload?.status || lastMessage.payload?.result?.status || '').toLowerCase();
      if (status === 'continue' || status === 'running' || status === 'pending' || status === '') {
        return true;
      }
    }
    
    return false;
  }, [messages]);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [filteredMessages.length]);

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <SearchFilterBar />
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto rounded-[28px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] via-[rgba(8,20,35,0.85)] to-[rgba(6,15,28,0.88)] p-6 shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(15,123,255,0.15),inset_0_1px_1px_rgba(255,255,255,0.08)] ring-1 ring-inset ring-white/5"
      >
        <div className="flex flex-col gap-5">
          {filteredMessages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-slate-400">
              <span className="text-3xl">✨</span>
              <p className="max-w-sm text-sm">
                Ready to launch. Describe a mission for the Galaxy Agent, or use quick commands below to explore diagnostics.
              </p>
            </div>
          ) : (
            <>
              {filteredMessages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  nextMessage={filteredMessages[index + 1]}
                  stepNumber={messageSteps.get(message.id)}
                />
              ))}
              
              {/* Loading indicator when waiting for agent response */}
              {isWaitingForResponse && !isTaskStopped && (
                <div className="ml-14 flex items-center gap-2 rounded-xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/30 to-blue-950/20 px-4 py-2.5 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                  <span className="text-xs font-medium text-cyan-300/90">
                    UFO is thinking...
                  </span>
                </div>
              )}
              
              {/* Task stopped indicator */}
              {isTaskStopped && (
                <div className="ml-14 flex items-center gap-2 rounded-xl border border-purple-400/20 bg-gradient-to-r from-purple-950/20 to-indigo-950/15 px-4 py-2.5 shadow-[0_0_16px_rgba(147,51,234,0.08)]">
                  <div className="h-2 w-2 rounded-full bg-purple-300/80 animate-pulse" />
                  <span className="text-xs font-medium text-purple-200/80">
                    Task stopped by user. Ready for new mission.
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <Composer />
    </div>
  );
};

export default ChatWindow;
