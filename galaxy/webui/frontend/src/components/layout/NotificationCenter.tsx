import React, { useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import clsx from 'clsx';
import { NotificationItem, useGalaxyStore } from '../../store/galaxyStore';

const severityStyles: Record<NotificationItem['severity'], { icon: React.ReactNode; className: string }> = {
  info: { icon: <Info className="h-4 w-4" aria-hidden />, className: 'border-cyan-400/40 bg-cyan-500/20 text-cyan-100' },
  success: { icon: <CheckCircle2 className="h-4 w-4" aria-hidden />, className: 'border-emerald-400/40 bg-emerald-500/20 text-emerald-100' },
  warning: { icon: <AlertCircle className="h-4 w-4" aria-hidden />, className: 'border-amber-400/40 bg-amber-500/20 text-amber-100' },
  error: { icon: <AlertCircle className="h-4 w-4" aria-hidden />, className: 'border-rose-400/40 bg-rose-500/20 text-rose-100' },
};

// Auto-dismiss delay in milliseconds
const AUTO_DISMISS_DELAY = 5000;

const NotificationCenter: React.FC = () => {
  const { notifications, dismissNotification, markNotificationRead } = useGalaxyStore(
    (state) => ({
      notifications: state.notifications,
      dismissNotification: state.dismissNotification,
      markNotificationRead: state.markNotificationRead,
    }),
  );

  // Auto-dismiss notifications after delay
  useEffect(() => {
    const timers: number[] = [];

    notifications.forEach((notification) => {
      const timer = setTimeout(() => {
        dismissNotification(notification.id);
      }, AUTO_DISMISS_DELAY);
      timers.push(timer);
    });

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [notifications, dismissNotification]);

  return (
    <div className="pointer-events-none fixed bottom-6 left-6 z-50 flex w-80 flex-col gap-3">
      <AnimatePresence>
        {notifications.map((notification) => {
          const style = severityStyles[notification.severity];
          return (
            <motion.div
              key={notification.id}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 10, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className={clsx('pointer-events-auto relative rounded-2xl border px-4 py-3 shadow-lg', style.className)}
              onMouseEnter={() => markNotificationRead(notification.id)}
            >
              <button
                type="button"
                className="absolute right-2 top-2 rounded-full border border-white/20 p-1 text-slate-200 transition hover:bg-white/10"
                onClick={() => dismissNotification(notification.id)}
              >
                <X className="h-3 w-3" aria-hidden />
              </button>
              <div className="flex items-start gap-3 pr-6">
                <div className="mt-1 flex-shrink-0">{style.icon}</div>
                <div className="flex-1 min-w-0 text-xs">
                  <div className="font-semibold text-white break-words">{notification.title}</div>
                  {notification.description && (
                    <div className="mt-1 text-[11px] text-slate-200/80 break-words">{notification.description}</div>
                  )}
                  <div className="mt-2 flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-slate-300/70">
                    <span className="truncate">{notification.source || 'system'}</span>
                    <span className="flex-shrink-0 ml-2">{new Date(notification.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default NotificationCenter;
