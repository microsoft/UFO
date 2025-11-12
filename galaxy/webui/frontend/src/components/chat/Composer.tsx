import React, { KeyboardEvent, useCallback, useState } from 'react';
import { Loader2, SendHorizonal, StopCircle, Wand2 } from 'lucide-react';
import clsx from 'clsx';
import { getWebSocketClient } from '../../services/websocket';
import { createClientId, useGalaxyStore } from '../../store/galaxyStore';

const QUICK_COMMANDS = [
  { label: '/reset', description: 'Reset the current session state.' },
  { label: '/replay', description: 'Start next session and replay last request.' },
];

const Composer: React.FC = () => {
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const { connected, session, ui, toggleComposerShortcuts, resetSessionState, messages, setTaskRunning, stopCurrentTask } = useGalaxyStore((state) => ({
    connected: state.connected,
    session: state.session,
    ui: state.ui,
    toggleComposerShortcuts: state.toggleComposerShortcuts,
    resetSessionState: state.resetSessionState,
    messages: state.messages,
    setTaskRunning: state.setTaskRunning,
    stopCurrentTask: state.stopCurrentTask,
  }));

  const handleCommand = useCallback(
    (command: string) => {
      switch (command) {
        case '/reset':
          getWebSocketClient().sendReset();
          resetSessionState({ clearHistory: true }); // Explicitly clear all history including constellations
          return true;
        case '/replay': {
          // Find the last user message
          const lastUserMessage = [...messages]
            .reverse()
            .find((msg) => msg.role === 'user');
          
          if (!lastUserMessage) {
            console.warn('No previous user message to replay');
            return true;
          }

          // Send next_session message
          getWebSocketClient().send({ type: 'next_session', timestamp: Date.now() });
          resetSessionState({ clearHistory: false }); // Keep constellation history

          // Wait a bit for session reset, then resend the last user request
          setTimeout(() => {
            getWebSocketClient().sendRequest(lastUserMessage.content);
            
            // Add the message to the store
            const store = useGalaxyStore.getState();
            const sessionId = store.ensureSession(session.id, session.displayName);
            const messageId = createClientId();
            
            store.addMessage({
              id: messageId,
              sessionId,
              role: 'user',
              kind: 'user',
              author: 'You',
              content: lastUserMessage.content,
              timestamp: Date.now(),
              status: 'sent',
            });
          }, 500); // 500ms delay to allow session reset to complete
          
          return true;
        }
        default:
          return false;
      }
    },
    [resetSessionState, messages, session.id, session.displayName],
  );

  const handleSubmit = useCallback(async () => {
    const trimmed = draft.trim();
    if (!trimmed || !connected) {
      return;
    }

    if (trimmed.startsWith('/')) {
      const handled = handleCommand(trimmed.toLowerCase());
      if (handled) {
        setDraft('');
        return;
      }
    }

    const store = useGalaxyStore.getState();
    const sessionId = store.ensureSession(session.id, session.displayName);
    const messageId = createClientId();

    store.addMessage({
      id: messageId,
      sessionId,
      role: 'user',
      kind: 'user',
      author: 'You',
      content: trimmed,
      timestamp: Date.now(),
      status: 'sent',
    });

    // Check if there are existing constellations - if yes, create a placeholder for the new request
    const currentConstellations = Object.keys(store.constellations);
    if (currentConstellations.length > 0) {
      // Create a temporary empty constellation to provide immediate visual feedback
      const tempConstellationId = `temp-${Date.now()}`;
      store.upsertConstellation({
        id: tempConstellationId,
        name: 'Loading...',
        status: 'pending',
        description: 'Waiting for constellation to be created...',
        taskIds: [],
        dag: { nodes: [], edges: [] },
        statistics: { total: 0, pending: 0, running: 0, completed: 0, failed: 0 },
        createdAt: Date.now(),
      });
      
      // Switch to the new empty constellation
      store.setActiveConstellation(tempConstellationId);
      console.log('📊 Created temporary constellation for new request');
    }

    setIsSending(true);
    setTaskRunning(true); // Mark task as running
    try {
      getWebSocketClient().sendRequest(trimmed);
    } catch (error) {
      console.error('Failed to send request', error);
      store.updateMessage(messageId, { status: 'error' });
      setTaskRunning(false); // Reset on error
    } finally {
      setDraft('');
      setIsSending(false);
    }
  }, [connected, draft, handleCommand, session.displayName, session.id, setTaskRunning]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Prevent Enter key if task is running
    if (ui.isTaskRunning) {
      if (event.key === 'Enter') {
        event.preventDefault();
      }
      return;
    }

    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative rounded-[30px] border border-white/10 bg-gradient-to-br from-[rgba(11,24,44,0.82)] to-[rgba(8,15,28,0.75)] p-4 shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(15,123,255,0.12),inset_0_1px_1px_rgba(255,255,255,0.06)] ring-1 ring-inset ring-white/5">{/* backdrop-blur-md removed for performance */}
      <div className="relative">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Ask Galaxy to orchestrate a new mission…' : 'Waiting for connection…'}
          rows={3}
          className="w-full resize-none rounded-3xl border border-white/5 bg-black/40 px-5 py-4 text-sm text-slate-100 placeholder:text-slate-500 shadow-[inset_0_2px_8px_rgba(0,0,0,0.3)] focus:border-white/15 focus:outline-none focus:ring-1 focus:ring-white/10 focus:shadow-[0_0_8px_rgba(15,123,255,0.08),inset_0_2px_8px_rgba(0,0,0,0.3)]"
          disabled={!connected || isSending || ui.isTaskRunning}
        />
        <div className="mt-3 flex items-center justify-between gap-2 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => toggleComposerShortcuts()}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 hover:border-white/30"
            >
              <Wand2 className="h-3 w-3" aria-hidden />
              Shortcuts
            </button>
            {ui.showComposerShortcuts && (
              <>
                {QUICK_COMMANDS.map((command) => (
                  <button
                    key={command.label}
                    type="button"
                    onClick={() => {
                      setDraft(command.label);
                      toggleComposerShortcuts();
                    }}
                    title={command.description}
                    className="rounded-full border border-white/10 bg-black/30 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-white/30 hover:bg-black/40"
                  >
                    {command.label}
                  </button>
                ))}
              </>
            )}
          </div>
          <button
            type="button"
            onClick={ui.isTaskRunning ? stopCurrentTask : handleSubmit}
            disabled={!connected || (!ui.isTaskRunning && draft.trim().length === 0) || isSending}
            className={clsx(
              'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold text-white transition-all duration-300',
              ui.isTaskRunning
                ? 'bg-gradient-to-br from-[rgba(80,20,30,0.75)] via-[rgba(100,25,35,0.70)] to-[rgba(80,20,30,0.75)] hover:from-[rgba(100,25,35,0.85)] hover:via-[rgba(120,30,40,0.80)] hover:to-[rgba(100,25,35,0.85)] border border-rose-900/40 hover:border-rose-800/50 shadow-[0_0_16px_rgba(139,0,0,0.25),0_4px_12px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.08)]'
                : 'bg-gradient-to-br from-[rgba(6,182,212,0.85)] via-[rgba(147,51,234,0.80)] to-[rgba(236,72,153,0.85)] hover:from-[rgba(6,182,212,0.95)] hover:via-[rgba(147,51,234,0.90)] hover:to-[rgba(236,72,153,0.95)] border border-cyan-400/30 hover:border-purple-400/40 shadow-[0_0_20px_rgba(6,182,212,0.3),0_0_30px_rgba(147,51,234,0.2),0_4px_16px_rgba(0,0,0,0.3),inset_0_1px_2px_rgba(255,255,255,0.15),inset_0_-1px_2px_rgba(0,0,0,0.2)] active:scale-95 active:shadow-[0_0_15px_rgba(6,182,212,0.4),0_2px_8px_rgba(0,0,0,0.4)]',
              (!connected || (!ui.isTaskRunning && draft.trim().length === 0) || isSending) && 'opacity-50 grayscale',
            )}
          >
            {isSending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Sending
              </>
            ) : ui.isTaskRunning ? (
              <>
                <StopCircle className="h-4 w-4" aria-hidden />
                Stop
              </>
            ) : (
              <>
                <SendHorizonal className="h-4 w-4" aria-hidden />
                Launch
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Composer;
