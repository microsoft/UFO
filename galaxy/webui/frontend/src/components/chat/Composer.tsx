import React, { KeyboardEvent, useCallback, useState } from 'react';
import { Loader2, SendHorizonal, Wand2 } from 'lucide-react';
import clsx from 'clsx';
import { getWebSocketClient } from '../../services/websocket';
import { createClientId, useGalaxyStore } from '../../store/galaxyStore';

const QUICK_COMMANDS = [
  { label: '/reset', description: 'Reset the current session state.' },
  { label: '/replay', description: 'Replay the last action sequence.' },
  { label: '/devices', description: 'Request a device status summary.' },
];

const Composer: React.FC = () => {
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);
  const { connected, session, ui, toggleComposerShortcuts, resetSessionState } = useGalaxyStore((state) => ({
    connected: state.connected,
    session: state.session,
    ui: state.ui,
    toggleComposerShortcuts: state.toggleComposerShortcuts,
    resetSessionState: state.resetSessionState,
  }));

  const handleCommand = useCallback(
    (command: string) => {
      switch (command) {
        case '/reset':
          getWebSocketClient().sendReset();
          resetSessionState();
          return true;
        case '/replay':
          getWebSocketClient().send({ type: 'replay_last', timestamp: Date.now() });
          return true;
        case '/devices':
          getWebSocketClient().send({ type: 'request_device_snapshot', timestamp: Date.now() });
          return true;
        default:
          return false;
      }
    },
    [resetSessionState],
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

    setIsSending(true);
    try {
      getWebSocketClient().sendRequest(trimmed);
    } catch (error) {
      console.error('Failed to send request', error);
      store.updateMessage(messageId, { status: 'error' });
    } finally {
      setDraft('');
      setIsSending(false);
    }
  }, [connected, draft, handleCommand, session.displayName, session.id]);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="compose-area-shadow relative rounded-[30px] border border-white/10 bg-black/40 p-4 backdrop-blur-md">
      <div className="relative">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={connected ? 'Ask Galaxy to orchestrate a new mission…' : 'Waiting for connection…'}
          rows={3}
          className="w-full resize-none rounded-3xl border border-white/5 bg-black/40 px-5 py-4 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-galaxy-blue/60"
          disabled={!connected || isSending}
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
            onClick={handleSubmit}
            disabled={!connected || draft.trim().length === 0 || isSending}
            className={clsx(
              'inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-galaxy-blue via-galaxy-purple to-galaxy-pink px-4 py-2 text-sm font-semibold text-white shadow-glow transition',
              (!connected || draft.trim().length === 0 || isSending) && 'opacity-50 grayscale',
            )}
          >
            {isSending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Sending
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
