import { useRef } from 'react';
import { Settings, X } from 'lucide-react';

interface SettingsDialogProps {
  taskReviewEnabled: boolean;
  onTaskReviewChange: (enabled: boolean) => void;
}

export default function SettingsDialog({ taskReviewEnabled, onTaskReviewChange }: SettingsDialogProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  return (
    <>
      <button
        type="button"
        aria-label="Settings"
        aria-haspopup="dialog"
        title="Settings"
        onClick={() => dialog.current?.showModal()}
        className="rounded-lg border border-white/10 bg-white/5 p-2 text-slate-300 hover:bg-white/10 hover:text-white"
      >
        <Settings className="h-5 w-5" aria-hidden />
      </button>
      <dialog
        ref={dialog}
        aria-labelledby="settings-title"
        className="w-96 max-w-[calc(100%-2rem)] rounded-xl border border-white/15 bg-slate-900 p-5 text-slate-100 shadow-xl backdrop:bg-black/60"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="settings-title" className="text-lg font-semibold">Settings</h2>
          <button
            type="button"
            aria-label="Close settings"
            onClick={() => dialog.current?.close()}
            className="rounded p-1.5 text-slate-400 hover:text-white"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        <label className="flex cursor-pointer items-center gap-3 text-sm font-medium">
          <input
            type="checkbox"
            checked={taskReviewEnabled}
            onChange={(event) => onTaskReviewChange(event.target.checked)}
            aria-describedby="task-review-description"
            className="h-4 w-4 accent-cyan-400"
          />
          Task result review
        </label>
        <p id="task-review-description" className="ml-7 mt-1 text-sm text-slate-300">
          Show “Review result” on finished tasks in this browser. It uses the results already returned by the device.
        </p>
      </dialog>
    </>
  );
}
