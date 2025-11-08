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
  const { messages, searchQuery, messageKind } = useGalaxyStore(
    (state) => ({
      messages: state.messages,
      searchQuery: state.ui.searchQuery,
      messageKind: state.ui.messageKindFilter,
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

  // Check if we're waiting for agent response
  const isWaitingForResponse = useMemo(() => {
    if (filteredMessages.length === 0) return false;
    
    const lastMessage = filteredMessages[filteredMessages.length - 1];
    
    // If last message is from user, we're waiting for response
    if (lastMessage.role === 'user') {
      return true;
    }
    
    // If last message is agent response but status is pending/running, still waiting
    if (lastMessage.role === 'assistant' && lastMessage.kind === 'response') {
      const status = lastMessage.payload?.status || lastMessage.payload?.result?.status;
      if (status && !['finish', 'completed', 'success', 'failed', 'error'].some(s => 
        status.toLowerCase().includes(s.toLowerCase())
      )) {
        return true;
      }
    }
    
    return false;
  }, [filteredMessages]);

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
        className="flex-1 overflow-y-auto rounded-3xl border border-white/5 bg-black/25 p-6 backdrop-blur-lg"
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
              {isWaitingForResponse && (
                <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/40 p-4 backdrop-blur-sm">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-400/30 shadow-lg">
                    <Loader2 className="h-5 w-5 animate-spin text-cyan-300" />
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium text-sm text-slate-200">
                      UFO is thinking...
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Processing your request
                    </span>
                  </div>
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
