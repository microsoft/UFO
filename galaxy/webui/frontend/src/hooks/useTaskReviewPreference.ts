import { useEffect, useState } from 'react';

const storageKey = 'galaxy.webui.taskResultReview';

function readPreference(): boolean {
  try {
    return window.localStorage.getItem(storageKey) === 'true';
  } catch {
    return false;
  }
}

export function useTaskReviewPreference() {
  const [enabled, setEnabled] = useState(readPreference);

  useEffect(() => {
    function syncPreference(event: StorageEvent) {
      if (event.key === storageKey || event.key === null) {
        setEnabled(readPreference());
      }
    }
    window.addEventListener('storage', syncPreference);
    setEnabled(readPreference());
    return () => window.removeEventListener('storage', syncPreference);
  }, []);

  function setPreference(value: boolean) {
    setEnabled(value);
    try {
      window.localStorage.setItem(storageKey, String(value));
    } catch {
      // The setting still applies to this page when browser storage is unavailable.
    }
  }

  return [enabled, setPreference] as const;
}
