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
    resetSessionState({ clearHistory: true }); // Clear all history including constellations
  };

  const handleNextSession = () => {
    getWebSocketClient().send({ type: 'next_session', timestamp: Date.now() });
    resetSessionState({ clearHistory: false }); // Keep constellation history
  };

  return (
    <div className="flex flex-col gap-4 rounded-[28px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] via-[rgba(8,20,35,0.85)] to-[rgba(6,15,28,0.88)] p-5 text-sm text-slate-100 shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(6,182,212,0.12),inset_0_1px_1px_rgba(255,255,255,0.08)] ring-1 ring-inset ring-white/5">
      <div className="flex items-start justify-start">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.5)]" aria-hidden />
          <div className="font-heading text-xl font-semibold tracking-tight text-white">{session.displayName}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <button
          type="button"
          onClick={handleReset}
          className="flex items-center gap-3 rounded-2xl border border-[rgba(10,186,181,0.4)] bg-gradient-to-r from-[rgba(10,186,181,0.15)] to-[rgba(6,182,212,0.15)] px-4 py-3 shadow-[0_4px_16px_rgba(0,0,0,0.25),0_0_15px_rgba(10,186,181,0.2),inset_0_1px_2px_rgba(255,255,255,0.1)] transition-all duration-200 hover:border-[rgba(10,186,181,0.6)] hover:from-[rgba(10,186,181,0.25)] hover:to-[rgba(6,182,212,0.25)] hover:shadow-[0_8px_24px_rgba(0,0,0,0.3),0_0_25px_rgba(10,186,181,0.3)]"
        >
          <RefreshCcw className="h-4 w-4 text-[rgb(10,186,181)]" aria-hidden />
          <div className="text-left">
            <div className="text-sm font-medium text-white">Reset Session</div>
            <div className="text-xs text-slate-400">Clear chat, tasks, and devices</div>
          </div>
        </button>

        <button
          type="button"
          onClick={handleNextSession}
          className="flex items-center gap-3 rounded-2xl border border-emerald-400/40 bg-gradient-to-r from-emerald-500/15 to-cyan-500/15 px-4 py-3 shadow-[0_4px_16px_rgba(0,0,0,0.25),0_0_15px_rgba(16,185,129,0.2),inset_0_1px_2px_rgba(255,255,255,0.1)] transition-all duration-200 hover:border-emerald-400/60 hover:from-emerald-500/25 hover:to-cyan-500/25 hover:shadow-[0_8px_24px_rgba(0,0,0,0.3),0_0_25px_rgba(16,185,129,0.3)]"
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
