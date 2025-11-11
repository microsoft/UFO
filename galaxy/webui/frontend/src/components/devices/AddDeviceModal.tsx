import React, { useState, useCallback, useMemo } from 'react';
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop - Solid color, no blur */}
      <div
        className="absolute inset-0 bg-slate-950/95"
        onClick={handleClose}
        aria-hidden
      />

      {/* Modal - Lightweight design */}
      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-cyan-500/30 bg-slate-900/95 p-8 shadow-2xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-cyan-400">
            Add New Device
          </h2>
          <button
            onClick={handleClose}
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-cyan-500/10 hover:text-cyan-300"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Device ID */}
          <div>
            <label className="mb-2 block text-sm font-medium text-cyan-300">
              Device ID <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={formData.device_id}
              onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
              placeholder="e.g., windows_agent_01"
              className={clsx(
                'w-full rounded-lg border bg-slate-800/80 px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors focus:outline-none',
                errors.device_id
                  ? 'border-rose-500/50 focus:border-rose-400 focus:ring-2 focus:ring-rose-400/30'
                  : 'border-slate-700 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30'
              )}
            />
            {errors.device_id && (
              <p className="mt-1.5 text-xs text-rose-400">{errors.device_id}</p>
            )}
          </div>

          {/* Server URL */}
          <div>
            <label className="mb-2 block text-sm font-medium text-cyan-300">
              Server URL <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={formData.server_url}
              onChange={(e) => setFormData({ ...formData, server_url: e.target.value })}
              placeholder="ws://localhost:5001/ws"
              className={clsx(
                'w-full rounded-lg border bg-slate-800/80 px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors focus:outline-none',
                errors.server_url
                  ? 'border-rose-500/50 focus:border-rose-400 focus:ring-2 focus:ring-rose-400/30'
                  : 'border-slate-700 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30'
              )}
            />
            {errors.server_url && (
              <p className="mt-1.5 text-xs text-rose-400">{errors.server_url}</p>
            )}
          </div>

          {/* OS */}
          <div>
            <label className="mb-2 block text-sm font-medium text-cyan-300">
              Operating System <span className="text-rose-400">*</span>
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
                'w-full rounded-lg border bg-slate-800/80 px-4 py-3 text-sm text-white transition-colors focus:outline-none',
                errors.os
                  ? 'border-rose-500/50 focus:border-rose-400 focus:ring-2 focus:ring-rose-400/30'
                  : 'border-slate-700 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30'
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
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
                autoFocus
              />
            )}
            
            {errors.os && <p className="mt-1.5 text-xs text-rose-400">{errors.os}</p>}
          </div>

          {/* Capabilities */}
          <div>
            <label className="mb-2 block text-sm font-medium text-cyan-300">
              Capabilities <span className="text-rose-400">*</span>
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
                className="flex-1 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
              />
              <button
                type="button"
                onClick={addCapability}
                className="rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-4 py-3 transition-colors hover:bg-emerald-500/30"
              >
                <Plus className="h-4 w-4 text-emerald-300" />
              </button>
            </div>
            {errors.capabilities && (
              <p className="mt-1 text-xs text-rose-400">{errors.capabilities}</p>
            )}
            {formData.capabilities.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {formData.capabilities.map((capability) => (
                  <span
                    key={capability}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-400/40 bg-indigo-500/20 px-3 py-1.5 text-xs font-medium text-indigo-300"
                  >
                    {capability}
                    <button
                      type="button"
                      onClick={() => removeCapability(capability)}
                      className="text-indigo-300 hover:text-rose-400"
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
            <label className="mb-1.5 block text-sm font-medium text-slate-300">
              Metadata <span className="text-xs text-slate-500">(Optional)</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={metadataKey}
                onChange={(e) => setMetadataKey(e.target.value)}
                placeholder="Key"
                className="flex-1 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm text-white placeholder-slate-500 transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
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
                className="flex-1 rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm text-white placeholder-slate-500 transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
              />
              <button
                type="button"
                onClick={addMetadata}
                className="rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-4 py-2.5 text-sm font-medium text-emerald-300 transition-colors hover:bg-emerald-500/30"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            {metadataEntries.length > 0 && (
              <div className="mt-2 space-y-1.5">
                {metadataEntries.map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-xs"
                  >
                    <span className="text-slate-300">
                      <span className="font-medium text-cyan-400">{key}:</span> {String(value)}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeMetadata(key)}
                      className="text-slate-400 hover:text-rose-400"
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
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
                Auto Connect
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.auto_connect}
                  onChange={(e) => setFormData({ ...formData, auto_connect: e.target.checked })}
                  className="h-4 w-4 cursor-pointer rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-2 focus:ring-cyan-400/30"
                />
                <span className="text-xs text-slate-400">Connect on startup</span>
              </label>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-300">
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
                className="w-full rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-sm text-white transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
              />
            </div>
          </div>

          {/* Submit Error */}
          {errors.submit && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {errors.submit}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1 rounded-lg border border-slate-700 bg-slate-800/60 px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 rounded-lg border border-cyan-400/40 bg-cyan-500/30 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-cyan-500/40 disabled:opacity-50"
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
  );
};

export default AddDeviceModal;
