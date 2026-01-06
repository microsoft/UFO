import React, { useMemo, useState } from 'react';
import { shallow } from 'zustand/shallow';
import { Cpu, WifiOff, Search, Clock, Bot, Plus } from 'lucide-react';
import clsx from 'clsx';
import { Device, DeviceStatus, useGalaxyStore } from '../../store/galaxyStore';
import AddDeviceModal, { DeviceFormData } from './AddDeviceModal';
import { getApiUrl } from '../../config/api';

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
        'group rounded-2xl border bg-gradient-to-br p-4 text-xs transition-all duration-300',
        // Default state with subtle glow
        'border-white/20 from-[rgba(25,40,60,0.75)] via-[rgba(20,35,52,0.7)] to-[rgba(15,28,45,0.75)]',
        'shadow-[0_4px_16px_rgba(0,0,0,0.3),0_0_8px_rgba(15,123,255,0.1),inset_0_1px_2px_rgba(255,255,255,0.1),inset_0_0_20px_rgba(15,123,255,0.03)]',
        // Hover state with enhanced glow
        'hover:border-white/35 hover:from-[rgba(28,45,65,0.85)] hover:via-[rgba(23,38,56,0.8)] hover:to-[rgba(18,30,48,0.85)]',
        'hover:shadow-[0_8px_24px_rgba(0,0,0,0.35),0_0_20px_rgba(15,123,255,0.2),0_0_30px_rgba(6,182,212,0.15),inset_0_1px_2px_rgba(255,255,255,0.15),inset_0_0_30px_rgba(15,123,255,0.06)]',
        'hover:translate-y-[-2px]',
        // Highlight state
        highlight && 'border-cyan-400/50 from-[rgba(6,182,212,0.2)] via-[rgba(15,123,255,0.15)] to-[rgba(15,28,45,0.8)] shadow-[0_0_30px_rgba(6,182,212,0.4),0_0_40px_rgba(6,182,212,0.25),0_4px_16px_rgba(0,0,0,0.3),inset_0_0_30px_rgba(6,182,212,0.1)]',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-mono text-sm text-white drop-shadow-[0_1px_4px_rgba(0,0,0,0.5)]">{device.name}</div>
          <div className="mt-1 flex items-center gap-2">
            <span className={clsx('h-2 w-2 rounded-full shadow-[0_0_6px_currentColor]', meta.dot)} aria-hidden />
            <span className={clsx('text-[11px] uppercase tracking-[0.2em]', meta.text)}>{meta.label}</span>
            {device.os && (
              <>
                <span className="text-slate-600">|</span>
                <span className="rounded-full border border-indigo-400/30 bg-indigo-500/20 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.15em] text-indigo-300 shadow-[0_0_8px_rgba(99,102,241,0.2),inset_0_1px_1px_rgba(255,255,255,0.1)]">
                  {device.os}
                </span>
              </>
            )}
          </div>
        </div>
        <Cpu className="h-4 w-4 text-slate-400 transition-all group-hover:text-cyan-400 group-hover:drop-shadow-[0_0_6px_rgba(6,182,212,0.5)]" aria-hidden />
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
  const [isModalOpen, setIsModalOpen] = useState(false);

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

  const handleAddDevice = async (deviceData: DeviceFormData) => {
    // Send device data to backend API
    try {
      const response = await fetch(getApiUrl('api/devices'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(deviceData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to add device');
      }

      // Success - modal will close automatically
    } catch (error) {
      // Rethrow to let modal handle the error display
      throw error;
    }
  };

  const existingDeviceIds = Object.keys(devices);

  return (
    <div className="flex h-full flex-col gap-4 rounded-[28px] border border-white/10 bg-gradient-to-br from-[rgba(11,30,45,0.88)] via-[rgba(8,20,35,0.85)] to-[rgba(6,15,28,0.88)] p-5 text-sm text-slate-100 shadow-[0_8px_32px_rgba(0,0,0,0.4),0_2px_8px_rgba(16,185,129,0.12),inset_0_1px_1px_rgba(255,255,255,0.08)] ring-1 ring-inset ring-white/5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bot className="h-5 w-5 text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" aria-hidden />
          <div className="font-heading text-xl font-semibold tracking-tight text-white">Device Agent</div>
          <div className="mt-0.5 rounded-lg border border-emerald-400/40 bg-gradient-to-r from-emerald-500/15 to-emerald-600/10 px-2.5 py-1 text-xs font-medium text-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.2),inset_0_1px_2px_rgba(255,255,255,0.1)]">
            {online}/{total} online
          </div>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="group rounded-lg border border-cyan-400/30 bg-gradient-to-r from-cyan-500/20 to-blue-600/15 p-2 shadow-[0_0_15px_rgba(6,182,212,0.2)] transition-all hover:from-cyan-500/30 hover:to-blue-600/25 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)]"
          aria-label="Add device"
          title="Add new device"
        >
          <Plus className="h-4 w-4 text-cyan-300 transition-transform group-hover:scale-110" />
        </button>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-gradient-to-r from-black/30 to-black/20 px-3 py-2.5 text-xs text-slate-300 shadow-[inset_0_2px_8px_rgba(0,0,0,0.3)] focus-within:border-white/15 focus-within:shadow-[0_0_8px_rgba(16,185,129,0.08),inset_0_2px_8px_rgba(0,0,0,0.3)]">
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

      <AddDeviceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleAddDevice}
        existingDeviceIds={existingDeviceIds}
      />
    </div>
  );
};

export default DevicePanel;
