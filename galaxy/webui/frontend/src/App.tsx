import React, { useEffect } from 'react';
import { shallow } from 'zustand/shallow';
import ChatWindow from './components/chat/ChatWindow';
import LeftSidebar from './components/layout/LeftSidebar';
import NotificationCenter from './components/layout/NotificationCenter';
import RightPanel from './components/layout/RightPanel';
import StarfieldOverlay from './components/layout/StarfieldOverlay';
import { useGalaxyStore } from './store/galaxyStore';

const statusLabels: Record<string, { label: string; color: string }> = {
  connecting: { label: 'Connecting', color: 'text-cyan-300' },
  connected: { label: 'Connected', color: 'text-emerald-300' },
  reconnecting: { label: 'Reconnecting', color: 'text-amber-300' },
  disconnected: { label: 'Disconnected', color: 'text-rose-300' },
  idle: { label: 'Idle', color: 'text-slate-400' },
};

const App: React.FC = () => {
  const { session, connectionStatus } = useGalaxyStore(
    (state) => ({
      session: state.session,
      connectionStatus: state.connectionStatus,
    }),
    shallow,
  );

  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;
    if (session.highContrast) {
      root.classList.add('high-contrast');
      body.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
      body.classList.remove('high-contrast');
    }
  }, [session.highContrast]);

  const status = statusLabels[connectionStatus] ?? statusLabels.idle;

  return (
    <div className={`relative min-h-screen w-full text-white galaxy-bg`}>
      <div className="pointer-events-none absolute inset-0 bg-starfield opacity-70" aria-hidden />
      <div className="pointer-events-none absolute inset-0">
        <StarfieldOverlay />
      </div>
      <div className="pointer-events-none absolute inset-0 noise-overlay" aria-hidden />

      <header className="relative z-20 border-b border-white/5 bg-transparent backdrop-blur-xl">
        <div className="mx-auto flex max-w-[2000px] items-center justify-between gap-6 px-6 py-4">
          <div className="flex items-center gap-4">
            <img
              src="/logo3.png"
              alt="UFO3 logo"
              className="h-16 w-16"
            />
            <div>
              <h1 className="font-heading text-2xl font-semibold tracking-tight text-white drop-shadow">
                UFO<sup className="ml-1 text-lg">3</sup> Galaxy Agent
              </h1>
              <p className="text-sm text-slate-300/80">
                Weaving the Digital Agent Galaxy
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-full border border-white/10 bg-galaxy-midnight/70 px-5 py-2 backdrop-blur">
            <span
              className={`h-2.5 w-2.5 rounded-full shadow-neon ${
                connectionStatus === 'connected'
                  ? 'bg-emerald-400 animate-pulse'
                  : connectionStatus === 'reconnecting'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-rose-400'
              }`}
            />
            <div className="flex flex-col leading-tight">
              <span className={`text-xs font-medium uppercase tracking-[0.2em] ${status.color}`}>
                {status.label}
              </span>
              <span className="text-[11px] text-slate-400/80">
                {session.displayName}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex h-[calc(100vh-88px)] max-w-[2000px] gap-4 px-6 pb-6 pt-4">
        <div className="hidden xl:flex xl:w-72 2xl:w-80">
          <LeftSidebar />
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <ChatWindow />
        </div>

        <div className="hidden lg:flex lg:w-[560px] 2xl:w-[640px]">
          <RightPanel />
        </div>
      </main>

      <NotificationCenter />
    </div>
  );
};

export default App;
