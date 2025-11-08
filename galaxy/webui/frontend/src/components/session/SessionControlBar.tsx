import React from 'react';
import { Download, Bug, RefreshCcw, Rocket, Sparkle, ServerCog } from 'lucide-react';
import { getWebSocketClient } from '../../services/websocket';
import { useGalaxyStore } from '../../store/galaxyStore';

const SessionControlBar: React.FC = () => {
  const {
    session,
    resetSessionState,
    toggleDebugMode,
    toggleHighContrast,
  } = useGalaxyStore((state) => ({
    session: state.session,
    resetSessionState: state.resetSessionState,
    toggleDebugMode: state.toggleDebugMode,
    toggleHighContrast: state.toggleHighContrast,
  }));

  const handleReset = () => {
    getWebSocketClient().sendReset();
    resetSessionState();
  };

  const handleNextSession = () => {
    getWebSocketClient().send({ type: 'next_session', timestamp: Date.now() });
    resetSessionState();
  };

  const handleExport = () => {
    const endpoint = session.id
      ? `/api/logs/export?sessionId=${encodeURIComponent(session.id)}`
      : '/api/logs/export';
    window.open(endpoint, '_blank');
  };

  return (
    <div className="glass-card flex flex-col gap-4 rounded-3xl p-5 text-sm text-slate-100">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-slate-400">
            Session
          </div>
          <div className="mt-1 text-lg font-semibold text-white">{session.displayName}</div>
          {session.id && (
            <div className="text-[11px] text-slate-400">ID: {session.id}</div>
          )}
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-slate-200"
          onClick={toggleHighContrast}
        >
          <Sparkle className="h-3 w-3" aria-hidden />
          {session.highContrast ? 'Standard' : 'High Contrast'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-2">
        <button
          type="button"
          onClick={handleReset}
          className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition hover:border-white/30 hover:bg-white/10"
        >
          <div className="flex items-center gap-3">
            <RefreshCcw className="h-4 w-4 text-cyan-300" aria-hidden />
            <div>
              <div className="text-sm font-medium text-white">Reset session</div>
              <div className="text-xs text-slate-400">Clear chat, tasks, and devices</div>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={handleNextSession}
          className="flex items-center justify-between rounded-2xl border border-white/10 bg-gradient-to-r from-galaxy-blue/20 to-galaxy-purple/20 px-4 py-3 transition hover:from-galaxy-blue/30 hover:to-galaxy-purple/30"
        >
          <div className="flex items-center gap-3">
            <Rocket className="h-4 w-4 text-emerald-300" aria-hidden />
            <div>
              <div className="text-sm font-medium text-white">Next session</div>
              <div className="text-xs text-slate-400">Launch with a fresh constellation</div>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={handleExport}
          className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition hover:border-white/30 hover:bg-white/10"
        >
          <div className="flex items-center gap-3">
            <Download className="h-4 w-4 text-sky-300" aria-hidden />
            <div>
              <div className="text-sm font-medium text-white">Export logs</div>
              <div className="text-xs text-slate-400">Download session transcript</div>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={toggleDebugMode}
          className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition hover:border-white/30 hover:bg-white/10"
        >
          <div className="flex items-center gap-3">
            <Bug className="h-4 w-4 text-amber-300" aria-hidden />
            <div>
              <div className="text-sm font-medium text-white">{session.debugMode ? 'Disable debug' : 'Enable debug'}</div>
              <div className="text-xs text-slate-400">Toggle verbose inspector output</div>
            </div>
          </div>
        </button>

        <button
          type="button"
          onClick={() => getWebSocketClient().send({ type: 'open_diagnostics', timestamp: Date.now() })}
          className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition hover:border-white/30 hover:bg-white/10"
        >
          <div className="flex items-center gap-3">
            <ServerCog className="h-4 w-4 text-purple-300" aria-hidden />
            <div>
              <div className="text-sm font-medium text-white">Diagnostics</div>
              <div className="text-xs text-slate-400">Open agent diagnostics panel</div>
            </div>
          </div>
        </button>
      </div>
    </div>
  );
};

export default SessionControlBar;
