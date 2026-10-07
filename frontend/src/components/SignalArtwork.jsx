import React from 'react';
import Icon from './Icon';

export default function SignalArtwork() {
  return <div className="signal-art" aria-hidden="true">
    <div className="signal-orbit orbit-outer" /><div className="signal-orbit orbit-inner" />
    <div className="signal-core"><Icon name="shield" /></div>
    <svg className="signal-wave" viewBox="0 0 600 160" fill="none">
      <path d="M0 80h50l8-10 8 20 8-45 8 70 8-85 8 100 8-100 8 90 8-55 8 15h30l8-10 8 20 8-55 8 90 8-110 8 120 8-90 8 60 8-40 8 15h130l8-20 8 35 8-65 8 90 8-110 8 120 8-100 8 70 8-40 8 20h40" stroke="currentColor" strokeWidth="1.5" />
    </svg>
    <span className="signal-caption">VOICE INTELLIGENCE / SIGNAL ANALYSIS</span>
  </div>;
}
