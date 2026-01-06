import React, { useEffect } from 'react';
import { shallow } from 'zustand/shallow';
import { X, Sidebar, LayoutDashboard } from 'lucide-react';
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
  const { session, connectionStatus, ui, toggleLeftDrawer, toggleRightDrawer } = useGalaxyStore(
    (state) => ({
      session: state.session,
      connectionStatus: state.connectionStatus,
      ui: state.ui,
      toggleLeftDrawer: state.toggleLeftDrawer,
      toggleRightDrawer: state.toggleRightDrawer,
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
      {/* Removed bg-starfield overlay for performance optimization */}
      {/* <div className="pointer-events-none absolute inset-0 bg-starfield opacity-70" aria-hidden /> */}
      <div className="pointer-events-none absolute inset-0">
        <StarfieldOverlay />
      </div>
      {/* Removed noise overlay for performance optimization */}
      {/* <div className="pointer-events-none absolute inset-0 noise-overlay" aria-hidden /> */}

      <header className="relative z-20 border-b border-white/5 bg-transparent">{/* backdrop-blur-xl removed for performance */}
        <div className="mx-auto flex max-w-[2560px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 py-3">
          {/* Mobile menu buttons */}
          <div className="flex items-center gap-2 lg:hidden">
            <button
              onClick={() => toggleLeftDrawer()}
              className="rounded-lg border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
              aria-label="Toggle left sidebar"
            >
              <Sidebar className="h-5 w-5" />
            </button>
            <button
              onClick={() => toggleRightDrawer()}
              className="rounded-lg border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:bg-white/10 hover:text-white"
              aria-label="Toggle right sidebar"
            >
              <LayoutDashboard className="h-5 w-5" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              {/* Removed blur animation for performance optimization */}
              {/* <div className="absolute inset-0 animate-pulse rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 blur-xl"></div> */}
              <img
                src="/logo3.png"
                alt="UFO3 logo"
                className="relative h-12 w-12 sm:h-16 sm:w-16 lg:h-20 lg:w-20 drop-shadow-[0_0_20px_rgba(6,182,212,0.3)]"
              />
            </div>
            <div className="hidden sm:block">
              <h1 className="font-heading text-xl sm:text-2xl lg:text-3xl font-bold tracking-tighter drop-shadow-[0_2px_12px_rgba(0,0,0,0.5)]">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-white to-purple-300">
                  UFO
                </span>
                <sup className="text-sm sm:text-base lg:text-lg font-semibold text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-white to-purple-300 ml-0.5">3</sup>
                <span className="ml-2 lg:ml-3 text-base sm:text-lg lg:text-xl font-normal tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 via-purple-200 to-cyan-200 hidden md:inline">
                  Weaving the Digital Agent Galaxy
                </span>
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3 sm:gap-4 rounded-full border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] to-[rgba(8,15,28,0.85)] px-3 sm:px-5 py-2 sm:py-2.5 shadow-[0_4px_16px_rgba(0,0,0,0.3),0_1px_4px_rgba(15,123,255,0.1),inset_0_1px_1px_rgba(255,255,255,0.06)] ring-1 ring-inset ring-white/5">{/* backdrop-blur removed */}
            <span
              className={`h-2 w-2 sm:h-2.5 sm:w-2.5 rounded-full shadow-neon ${
                connectionStatus === 'connected'
                  ? 'bg-emerald-400 animate-pulse'
                  : connectionStatus === 'reconnecting'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-rose-400'
              }`}
            />
            <div className="flex flex-col leading-tight">
              <span className={`text-[10px] sm:text-xs font-medium uppercase tracking-[0.2em] ${status.color}`}>
                {status.label}
              </span>
              <span className="text-[9px] sm:text-[11px] text-slate-400/80">
                {session.displayName}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto flex h-[calc(100vh-94px)] max-w-[2560px] gap-4 px-4 sm:px-6 lg:px-8 pb-6 pt-1">
        {/* Left sidebar drawer for mobile/tablet */}
        {ui.showLeftDrawer && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => toggleLeftDrawer(false)}
            />
            <div className="absolute left-0 top-0 h-full w-80 max-w-[85vw] bg-[#0a0e1a] shadow-2xl animate-slide-in-left">
              <div className="flex items-center justify-between border-b border-white/10 p-4">
                <h2 className="text-lg font-semibold text-white">Devices</h2>
                <button
                  onClick={() => toggleLeftDrawer(false)}
                  className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/5 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="h-[calc(100%-64px)] overflow-y-auto">
                <LeftSidebar />
              </div>
            </div>
          </div>
        )}

        {/* Right sidebar drawer for mobile/tablet */}
        {ui.showRightDrawer && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => toggleRightDrawer(false)}
            />
            <div className="absolute right-0 top-0 h-full w-96 max-w-[90vw] bg-[#0a0e1a] shadow-2xl animate-slide-in-right">
              <div className="flex items-center justify-between border-b border-white/10 p-4">
                <h2 className="text-lg font-semibold text-white">Constellation</h2>
                <button
                  onClick={() => toggleRightDrawer(false)}
                  className="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/5 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="h-[calc(100%-64px)] overflow-y-auto">
                <RightPanel />
              </div>
            </div>
          </div>
        )}

        {/* Desktop left sidebar */}
        <div className="hidden xl:flex xl:w-72 2xl:w-80">
          <LeftSidebar />
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <ChatWindow />
        </div>

        {/* Desktop right sidebar */}
        <div className="hidden lg:flex lg:w-[520px] xl:w-[560px] 2xl:w-[640px]">
          <RightPanel />
        </div>
      </main>

      <NotificationCenter />
    </div>
  );
};

export default App;
