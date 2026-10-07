import React from 'react';

const paths = {
  menu: 'M4 6h16 M4 12h16 M4 18h16',
  shield: 'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Z M9 12l2 2 4-4',
  prompt: 'M4 4h16v12H9l-5 4V4Z M8 8h8 M8 12h5',
  voice: 'M4 10v4 M8 6v12 M12 3v18 M16 7v10 M20 10v4',
  incident: 'm12 3 10 18H2L12 3Z M12 9v5 M12 17v.1',
  audit: 'M6 3h9l4 4v14H6V3Z M14 3v5h5 M9 12h7 M9 16h7',
  policy: 'M4 6h16 M4 12h16 M4 18h16 M8 4v4 M16 10v4 M10 16v4',
  chart: 'M4 3v17h17 M8 16v-5 M13 16V7 M18 16V4',
  pulse: 'M2 12h5l3-8 4 16 3-8h5',
  logout: 'M10 4H4v16h6 M9 12h12 M17 8l4 4-4 4',
  arrow: 'M4 12h16 M15 7l5 5-5 5',
  upload: 'M12 16V3 M7 8l5-5 5 5 M4 16v5h16v-5',
  lock: 'M5 10h14v11H5V10Z M8 10V6a4 4 0 0 1 8 0v4 M12 14v3',
  search: 'M20 20l-5-5 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
};
export default function Icon({ name = 'shield', className = '' }) {
  return <svg className={`ui-icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.shield} /></svg>;
}
