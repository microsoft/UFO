import React, { useMemo, useState } from 'react';
import { shallow } from 'zustand/shallow';
import { Cpu, WifiOff, Search, Activity, Clock } from 'lucide-react';
import clsx from 'clsx';
import { Device, DeviceStatus, useGalaxyStore } from '../../store/galaxyStore';

const statusMeta: Record<DeviceStatus, { label: string; dot: string; text: string }> = {
  connected: { label: 'Connected', dot: 'bg-emerald-400', text: 'text-emerald-300' },
  idle: { label: 'Idle', dot: 'bg-cyan-400', text: 'text-cyan-200' },
  busy: { label: 'Busy', dot: 'bg-amber-400', text: 'text-amber-200' },
  connecting: { label: 'Connecting', dot: 'bg-blue-400', text: 'text-blue-200' },
  failed: { label: 'Failed', dot: 'bg-rose-500', text: 'text-rose-200' },
  disconnected: { label: 'Disconnected', dot: 'bg-slate-500', text: 'text-slate-300' },
  offline: { label: 'Offline', dot: 'bg-slate-600', text: 'text-slate-400' },
  unknown: { label: 'Unknown', dot: 'bg-slate-600', text: 'text-slate-400' },
};

const formatHeartbeat = (heartbeat?: string | null) => {
  if (!heartbeat) {
    return 'No heartbeat yet';
  }
  const parsed = Date.parse(heartbeat);
  if (Number.isNaN(parsed)) {
    return heartbeat;
  }
  const delta = Date.now() - parsed;
  if (delta < 60_000) {
    return 'Just now';
  }
  const minutes = Math.round(delta / 60_000);
  if (minutes < 60) {
    return `${minutes} min ago`;
  }
  const hours = Math.round(minutes / 60);
  return `${hours} hr ago`;
};

const DeviceCard: React.FC<{ device: Device }> = ({ device }) => {
  const meta = statusMeta[device.status] || statusMeta.unknown;
  const highlight = device.highlightUntil && device.highlightUntil > Date.now();

  return (
    <div
      className={clsx(
        'rounded-2xl border border-white/10 bg-white/5 p-4 text-xs transition hover:border-white/30',
        highlight && 'shadow-neon',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-mono text-sm text-white">{device.name}</div>
          <div className="mt-1 flex items-center gap-2">
            <span className={clsx('h-2 w-2 rounded-full', meta.dot)} aria-hidden />
            <span className={clsx('text-[11px] uppercase tracking-[0.2em]', meta.text)}>{meta.label}</span>
            {device.os && (
              <>
                <span className="text-slate-600">|</span>
                <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.15em] text-indigo-300">
                  {device.os}
                </span>
              </>
            )}
          </div>
        </div>
        <Cpu className="h-4 w-4 text-slate-400" aria-hidden />
      </div>
      <div className="mt-3 grid gap-2 text-[11px] text-slate-300">
        {device.capabilities && device.capabilities.length > 0 && (
          <div>Capabilities: {device.capabilities.join(', ')}</div>
        )}
        <div className="flex items-center gap-2 text-slate-400">
          <Clock className="h-3 w-3" aria-hidden />
          {formatHeartbeat(device.lastHeartbeat)}
        </div>
        {device.metadata && device.metadata.region && (
          <div>Region: {device.metadata.region}</div>
        )}
      </div>
    </div>
  );
};

const DevicePanel: React.FC = () => {
  const { devices } = useGalaxyStore(
    (state) => ({
      devices: state.devices,
    }),
    shallow,
  );

  const [query, setQuery] = useState('');

  const deviceList = useMemo(() => {
    const list = Object.values(devices);
    if (!query) {
      return list;
    }
    const normalized = query.toLowerCase();
    return list.filter((device) =>
      [device.name, device.id, device.os, device.metadata?.region]
        .filter(Boolean)
        .map((value) => String(value).toLowerCase())
        .some((value) => value.includes(normalized)),
    );
  }, [devices, query]);

  const total = deviceList.length;
  const online = deviceList.filter((device) => device.status === 'connected' || device.status === 'idle' || device.status === 'busy').length;

  return (
    <div className="glass-card flex h-full flex-col gap-4 rounded-3xl p-5 text-sm text-slate-100">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-slate-400">
            Devices
          </div>
          <div className="text-lg font-semibold text-white">{online}/{total} online</div>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-slate-300">
          <Activity className="h-3 w-3" aria-hidden />
          Fleet
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-xs text-slate-300">
        <Search className="h-3.5 w-3.5" aria-hidden />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by id, region, or OS"
          className="w-full bg-transparent focus:outline-none"
        />
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto">
        {deviceList.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-xs text-slate-400">
            <WifiOff className="h-5 w-5" aria-hidden />
            No devices reported yet.
          </div>
        ) : (
          deviceList.map((device) => <DeviceCard key={device.id} device={device} />)
        )}
      </div>
    </div>
  );
};

export default DevicePanel;
