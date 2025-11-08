import React, { useEffect, useMemo, useRef } from 'react';
import { shallow } from 'zustand/shallow';
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
            filteredMessages.map((message) => <MessageBubble key={message.id} message={message} />)
          )}
        </div>
      </div>
      <Composer />
    </div>
  );
};

export default ChatWindow;
