import React from 'react';
import { RefreshCcw, Rocket } from 'lucide-react';
import { getWebSocketClient } from '../../services/websocket';
import { useGalaxyStore } from '../../store/galaxyStore';

const SessionControlBar: React.FC = () => {
  const {
    session,
    resetSessionState,
  } = useGalaxyStore((state) => ({
    session: state.session,
    resetSessionState: state.resetSessionState,
  }));

  const handleReset = () => {
    getWebSocketClient().sendReset();
    resetSessionState();
  };

  const handleNextSession = () => {
    getWebSocketClient().send({ type: 'next_session', timestamp: Date.now() });
    resetSessionState();
  };

  return (
    <div className="glass-card flex flex-col gap-4 rounded-3xl p-5 text-sm text-slate-100">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-slate-400">
            Session
          </div>
          <div className="mt-1 text-lg font-semibold text-white">{session.displayName}</div>
        </div>
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
      </div>
    </div>
  );
};

export default SessionControlBar;
