import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { X, Plus, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface AddDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (device: DeviceFormData) => Promise<void>;
  existingDeviceIds: string[];
}

export interface DeviceFormData {
  device_id: string;
  server_url: string;
  os: string;
  capabilities: string[];
  metadata?: Record<string, any>;
  auto_connect?: boolean;
  max_retries?: number;
}

const AddDeviceModal: React.FC<AddDeviceModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  existingDeviceIds,
}) => {
  const [formData, setFormData] = useState<DeviceFormData>({
    device_id: '',
    server_url: '',
    os: '',
    capabilities: [],
    metadata: {},
    auto_connect: true,
    max_retries: 5,
  });

  const [capabilityInput, setCapabilityInput] = useState('');
  const [metadataKey, setMetadataKey] = useState('');
  const [metadataValue, setMetadataValue] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCustomOS, setShowCustomOS] = useState(false);
  const [customOS, setCustomOS] = useState('');

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Device ID validation
    if (!formData.device_id.trim()) {
      newErrors.device_id = 'Device ID is required';
    } else if (existingDeviceIds.includes(formData.device_id.trim())) {
      newErrors.device_id = 'Device ID already exists';
    }

    // Server URL validation
    if (!formData.server_url.trim()) {
      newErrors.server_url = 'Server URL is required';
    } else if (!formData.server_url.match(/^wss?:\/\/.+/)) {
      newErrors.server_url = 'Invalid WebSocket URL (must start with ws:// or wss://)';
    }

    // OS validation
    if (!formData.os.trim()) {
      newErrors.os = 'OS is required';
    }

    // Capabilities validation
    if (formData.capabilities.length === 0) {
      newErrors.capabilities = 'At least one capability is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      handleClose();
    } catch (error) {
      setErrors({ submit: error instanceof Error ? error.message : 'Failed to add device' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = useCallback(() => {
    setFormData({
      device_id: '',
      server_url: '',
      os: '',
      capabilities: [],
      metadata: {},
      auto_connect: true,
      max_retries: 5,
    });
    setCapabilityInput('');
    setMetadataKey('');
    setMetadataValue('');
    setErrors({});
    setIsSubmitting(false);
    setShowCustomOS(false);
    setCustomOS('');
    onClose();
  }, [onClose]);

  const addCapability = useCallback(() => {
    if (capabilityInput.trim() && !formData.capabilities.includes(capabilityInput.trim())) {
      setFormData((prev) => ({
        ...prev,
        capabilities: [...prev.capabilities, capabilityInput.trim()],
      }));
      setCapabilityInput('');
      setErrors((prev) => ({ ...prev, capabilities: '' }));
    }
  }, [capabilityInput, formData.capabilities]);

  const removeCapability = useCallback((capability: string) => {
    setFormData((prev) => ({
      ...prev,
      capabilities: prev.capabilities.filter((c) => c !== capability),
    }));
  }, []);

  const addMetadata = useCallback(() => {
    if (metadataKey.trim() && metadataValue.trim()) {
      setFormData((prev) => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          [metadataKey.trim()]: metadataValue.trim(),
        },
      }));
      setMetadataKey('');
      setMetadataValue('');
    }
  }, [metadataKey, metadataValue]);

  const removeMetadata = useCallback((key: string) => {
    setFormData((prev) => {
      const newMetadata = { ...prev.metadata };
      delete newMetadata[key];
      return {
        ...prev,
        metadata: newMetadata,
      };
    });
  }, []);

  // Memoize metadata entries to avoid re-renders
  const metadataEntries = useMemo(() => 
    Object.entries(formData.metadata || {}),
    [formData.metadata]
  );

  // Add ESC key listener to close modal
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen && !isSubmitting) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
    }

    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [isOpen, isSubmitting, handleClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop - Soft gradient overlay */}
      <div
        className="absolute inset-0 bg-gradient-to-br from-slate-950/96 via-indigo-950/92 to-slate-950/96"
        onClick={handleClose}
        aria-hidden
      />

      {/* Modal - Soft futuristic design with gradient borders */}
      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-indigo-400/20 bg-gradient-to-br from-slate-900/96 via-slate-900/94 to-indigo-950/96 p-8 shadow-[0_0_50px_rgba(99,102,241,0.15),0_20px_60px_rgba(0,0,0,0.5)]">
        {/* Subtle inner glow */}
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-indigo-500/5 via-transparent to-blue-500/5 pointer-events-none" />
        
        {/* Content wrapper */}
        <div className="relative">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-300 via-blue-300 to-cyan-300 bg-clip-text text-transparent">
              Add New Device
            </h2>
            <button
              onClick={handleClose}
              className="rounded-lg p-2 text-slate-400 transition-all hover:bg-indigo-500/10 hover:text-indigo-300 hover:shadow-[0_0_15px_rgba(99,102,241,0.2)]"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Device ID */}
          <div>
            <label className="mb-2 block text-sm font-medium bg-gradient-to-r from-indigo-300 to-blue-300 bg-clip-text text-transparent">
              Device ID <span className="text-rose-300/80">*</span>
            </label>
            <input
              type="text"
              value={formData.device_id}
              onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
              placeholder="e.g., windows_agent_01"
              className={clsx(
                'w-full rounded-lg border bg-slate-800/60 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 transition-all focus:outline-none focus:bg-slate-800/80',
                errors.device_id
                  ? 'border-rose-400/40 focus:border-rose-300/60 focus:ring-2 focus:ring-rose-400/20 focus:shadow-[0_0_15px_rgba(251,113,133,0.15)]'
                  : 'border-slate-600/50 focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-400/20 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]'
              )}
            />
            {errors.device_id && (
              <p className="mt-1.5 text-xs text-rose-300/90">{errors.device_id}</p>
            )}
          </div>

          {/* Server URL */}
          <div>
            <label className="mb-2 block text-sm font-medium bg-gradient-to-r from-indigo-300 to-blue-300 bg-clip-text text-transparent">
              Server URL <span className="text-rose-300/80">*</span>
            </label>
            <input
              type="text"
              value={formData.server_url}
              onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
              placeholder="ws://localhost:5001/ws"
              className={clsx(
                'w-full rounded-lg border bg-slate-800/60 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 transition-all focus:outline-none focus:bg-slate-800/80',
                errors.server_url
                  ? 'border-rose-400/40 focus:border-rose-300/60 focus:ring-2 focus:ring-rose-400/20 focus:shadow-[0_0_15px_rgba(251,113,133,0.15)]'
                  : 'border-slate-600/50 focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-400/20 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]'
              )}
            />
            {errors.server_url && (
              <p className="mt-1.5 text-xs text-rose-300/90">{errors.server_url}</p>
            )}
          </div>

          {/* OS */}
          <div>
            <label className="mb-2 block text-sm font-medium bg-gradient-to-r from-indigo-300 to-blue-300 bg-clip-text text-transparent">
              Operating System <span className="text-rose-300/80">*</span>
            </label>
            <select
              value={showCustomOS ? 'custom' : formData.os}
              onChange={(e) => {
                const value = e.target.value;
                if (value === 'custom') {
                  setShowCustomOS(true);
                  setFormData({ ...formData, os: customOS });
                } else {
                  setShowCustomOS(false);
                  setCustomOS('');
                  setFormData({ ...formData, os: value });
                }
              }}
              className={clsx(
                'w-full rounded-lg border bg-slate-800/60 px-4 py-3 text-sm text-slate-100 transition-all focus:outline-none focus:bg-slate-800/80',
                errors.os
                  ? 'border-rose-400/40 focus:border-rose-300/60 focus:ring-2 focus:ring-rose-400/20 focus:shadow-[0_0_15px_rgba(251,113,133,0.15)]'
                  : 'border-slate-600/50 focus:border-indigo-400/50 focus:ring-2 focus:ring-indigo-400/20 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]'
              )}
            >
              <option value="" disabled className="bg-slate-900">
                Select OS
              </option>
              <option value="windows" className="bg-slate-900">
                Windows
              </option>
              <option value="linux" className="bg-slate-900">
                Linux
              </option>
              <option value="macos" className="bg-slate-900">
                macOS
              </option>
              <option value="custom" className="bg-slate-900">
                Custom / Other...
              </option>
            </select>
            
            {/* Custom OS Input */}
            {showCustomOS && (
              <input
                type="text"
                value={customOS}
                onChange={(e) => {
                  setCustomOS(e.target.value);
                  setFormData({ ...formData, os: e.target.value });
                }}
                placeholder="Enter custom OS name"
                className="mt-2 w-full rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 transition-all focus:border-indigo-400/50 focus:outline-none focus:ring-2 focus:ring-indigo-400/20 focus:bg-slate-800/80 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]"
                autoFocus
              />
            )}
            
            {errors.os && <p className="mt-1.5 text-xs text-rose-300/90">{errors.os}</p>}
          </div>

          {/* Capabilities */}
          <div>
            <label className="mb-2 block text-sm font-medium bg-gradient-to-r from-indigo-300 to-blue-300 bg-clip-text text-transparent">
              Capabilities <span className="text-rose-300/80">*</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={capabilityInput}
                onChange={(e) => setCapabilityInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addCapability();
                  }
                }}
                placeholder="e.g., web_browsing"
                className="flex-1 rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 transition-all focus:border-indigo-400/50 focus:outline-none focus:ring-2 focus:ring-indigo-400/20 focus:bg-slate-800/80 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]"
              />
              <button
                type="button"
                onClick={addCapability}
                className="rounded-lg border border-emerald-400/30 bg-emerald-500/15 px-4 py-3 transition-all hover:bg-emerald-500/25 hover:border-emerald-400/40 hover:shadow-[0_0_15px_rgba(52,211,153,0.15)]"
              >
                <Plus className="h-4 w-4 text-emerald-300/90" />
              </button>
            </div>
            {errors.capabilities && (
              <p className="mt-1 text-xs text-rose-300/90">{errors.capabilities}</p>
            )}
            {formData.capabilities.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {formData.capabilities.map((capability) => (
                  <span
                    key={capability}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-400/30 bg-indigo-500/15 px-3 py-1.5 text-xs font-medium text-indigo-200/90 shadow-[0_0_10px_rgba(129,140,248,0.1)]"
                  >
                    {capability}
                    <button
                      type="button"
                      onClick={() => removeCapability(capability)}
                      className="text-indigo-300/70 hover:text-rose-300/90 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Metadata (Optional) */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300/90">
              Metadata <span className="text-xs text-slate-500">(Optional)</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={metadataKey}
                onChange={(e) => setMetadataKey(e.target.value)}
                placeholder="Key"
                className="flex-1 rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 transition-all focus:border-indigo-400/50 focus:outline-none focus:ring-2 focus:ring-indigo-400/20 focus:bg-slate-800/80 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]"
              />
              <input
                type="text"
                value={metadataValue}
                onChange={(e) => setMetadataValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addMetadata();
                  }
                }}
                placeholder="Value"
                className="flex-1 rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 transition-all focus:border-indigo-400/50 focus:outline-none focus:ring-2 focus:ring-indigo-400/20 focus:bg-slate-800/80 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]"
              />
              <button
                type="button"
                onClick={addMetadata}
                className="rounded-lg border border-emerald-400/30 bg-emerald-500/15 px-4 py-2.5 text-sm font-medium text-emerald-300/90 transition-all hover:bg-emerald-500/25 hover:border-emerald-400/40 hover:shadow-[0_0_15px_rgba(52,211,153,0.15)]"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            {metadataEntries.length > 0 && (
              <div className="mt-2 space-y-1.5">
                {metadataEntries.map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-lg border border-slate-600/40 bg-slate-800/50 px-3 py-2 text-xs"
                  >
                    <span className="text-slate-300/90">
                      <span className="font-medium text-indigo-300/90">{key}:</span> {String(value)}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeMetadata(key)}
                      className="text-slate-400 hover:text-rose-300/90 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Advanced Options */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300/90">
                Auto Connect
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.auto_connect}
                  onChange={(e) => setFormData({ ...formData, auto_connect: e.target.checked })}
                  className="h-4 w-4 cursor-pointer rounded border-slate-600 bg-slate-800/60 text-indigo-500 focus:ring-2 focus:ring-indigo-400/20"
                />
                <span className="text-xs text-slate-400">Connect on startup</span>
              </label>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300/90">
                Max Retries
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={formData.max_retries}
                onChange={(e) =>
                  setFormData({ ...formData, max_retries: parseInt(e.target.value) || 5 })
                }
                className="w-full rounded-lg border border-slate-600/50 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-100 transition-all focus:border-indigo-400/50 focus:outline-none focus:ring-2 focus:ring-indigo-400/20 focus:bg-slate-800/80 focus:shadow-[0_0_15px_rgba(129,140,248,0.1)]"
              />
            </div>
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200/90">
              {errors.submit}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1 rounded-lg border border-slate-600/50 bg-slate-800/50 px-4 py-3 text-sm font-medium text-slate-300/90 transition-all hover:bg-slate-800/70 hover:border-slate-500/60 disabled:opacity-50 hover:shadow-[0_0_15px_rgba(100,116,139,0.1)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded-lg border border-indigo-400/30 bg-gradient-to-r from-indigo-500/25 to-blue-500/25 px-4 py-3 text-sm font-semibold text-white transition-all hover:from-indigo-500/35 hover:to-blue-500/35 hover:border-indigo-400/40 disabled:opacity-50 hover:shadow-[0_0_20px_rgba(99,102,241,0.2)]"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Adding...
                </span>
              ) : (
                'Add Device'
              )}
            </button>
          </div>
        </form>
        </div>
      </div>
    </div>
  );
};

export default AddDeviceModal;
