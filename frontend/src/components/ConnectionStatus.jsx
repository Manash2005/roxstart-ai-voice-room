import React from 'react';
import { Wifi, WifiOff, AlertCircle, RefreshCw } from 'lucide-react';

/**
 * Visual badge indicating current WebRTC room connection state.
 *
 * Designed with minimalist frosted glass and semantic color cues:
 * - Connected: #4F7D32 (Forest Green)
 * - Connecting / Reconnecting: #F5B52E & #FFD16A (Amber & Cream)
 * - Error: #D9361E (Crimson Rust)
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
      bg: 'bg-[#4F7D32]/15 border-[#4F7D32]/40 text-[#a3d98b]',
      dot: 'bg-[#4F7D32] animate-pulse',
    },
    connecting: {
      label: 'Connecting...',
      icon: RefreshCw,
      bg: 'bg-[#F5B52E]/15 border-[#F5B52E]/40 text-[#FFD16A]',
      dot: 'bg-[#FFD16A] animate-ping',
      spin: true,
    },
    reconnecting: {
      label: 'Reconnecting...',
      icon: RefreshCw,
      bg: 'bg-[#F5B52E]/20 border-[#F5B52E]/50 text-[#FFD16A]',
      dot: 'bg-[#F5B52E] animate-ping',
      spin: true,
    },
    error: {
      label: error || 'Connection Error',
      icon: AlertCircle,
      bg: 'bg-[#D9361E]/15 border-[#D9361E]/40 text-[#ff8e7d]',
      dot: 'bg-[#D9361E]',
    },
    disconnected: {
      label: 'Disconnected',
      icon: WifiOff,
      bg: 'bg-white/[0.04] border-white/10 text-stone-400',
      dot: 'bg-stone-500',
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
