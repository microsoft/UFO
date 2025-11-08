import React from 'react';
import { RefreshCcw, Rocket, Sparkles } from 'lucide-react';
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
      <div className="flex items-start justify-start">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-cyan-400" aria-hidden />
          <div className="font-heading text-xl font-semibold tracking-tight text-white">{session.displayName}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <button
          type="button"
          onClick={handleReset}
          className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 transition hover:border-white/30 hover:bg-white/10"
        >
          <RefreshCcw className="h-4 w-4 text-cyan-300" aria-hidden />
          <div className="text-left">
            <div className="text-sm font-medium text-white">Reset Session</div>
            <div className="text-xs text-slate-400">Clear chat, tasks, and devices</div>
          </div>
        </button>

        <button
          type="button"
          onClick={handleNextSession}
          className="flex items-center gap-3 rounded-2xl border border-emerald-400/30 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 px-4 py-3 transition hover:border-emerald-400/50 hover:from-emerald-500/30 hover:to-cyan-500/30"
        >
          <Rocket className="h-4 w-4 text-emerald-300" aria-hidden />
          <div className="text-left">
            <div className="text-sm font-medium text-white">Next Session</div>
            <div className="text-xs text-slate-400">Launch with a fresh constellation</div>
          </div>
        </button>
      </div>
    </div>
  );
};

export default SessionControlBar;
