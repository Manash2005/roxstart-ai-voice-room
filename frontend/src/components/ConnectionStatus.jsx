import React from 'react';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';

/**
 * Visual badge indicating current WebRTC room connection state.
 *
 * @param {Object} props
 * @param {'connecting'|'connected'|'reconnecting'|'disconnected'|'error'} props.state
 * @param {string} [props.error]
 */
export default function ConnectionStatus({ state, error }) {
  const configs = {
    connected: {
      label: 'Connected',
      icon: Wifi,
      bg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300',
      dot: 'bg-emerald-400 animate-pulse',
    },
    connecting: {
      label: 'Connecting...',
      icon: RefreshCw,
      bg: 'bg-purple-500/15 border-purple-500/40 text-purple-300',
      dot: 'bg-purple-400 animate-ping',
      spin: true,
    },
    reconnecting: {
      label: 'Reconnecting...',
      icon: RefreshCw,
      bg: 'bg-amber-500/15 border-amber-500/40 text-amber-300',
      dot: 'bg-amber-400 animate-ping',
      spin: true,
    },
    error: {
      label: error || 'Connection Error',
      icon: AlertCircle,
      bg: 'bg-rose-500/15 border-rose-500/40 text-rose-300',
      dot: 'bg-rose-400',
    },
    disconnected: {
      label: 'Disconnected',
      icon: WifiOff,
      bg: 'bg-slate-700/30 border-slate-700 text-slate-400',
      dot: 'bg-slate-500',
    },
  };

  const config = configs[state] || configs.disconnected;
  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border backdrop-blur-md transition-all ${config.bg}`}
      role="status"
      aria-label={`Connection state: ${config.label}`}
    >
      <span className={`w-2 h-2 rounded-full ${config.dot}`} />
      <Icon className={`w-3.5 h-3.5 ${config.spin ? 'animate-spin' : ''}`} />
      <span>{config.label}</span>
    </div>
  );
}
