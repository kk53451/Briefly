// Briefly — minimal, editorial icon set (hand-picked line icons).
// Keep strokes aligned with the ink color for consistency with the type.

const Icon = ({ name, size = 20, color = 'currentColor', strokeWidth = 1.6 }) => {
  const s = { width: size, height: size, flexShrink: 0 };
  const p = { fill: 'none', stroke: color, strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round' };
  switch (name) {
    case 'home':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M3 11l9-7 9 7v9a1 1 0 01-1 1h-5v-6h-6v6H4a1 1 0 01-1-1z"/></svg>);
    case 'newspaper':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M4 5h14v14H6a2 2 0 01-2-2z"/><path {...p} d="M18 8h2v9a2 2 0 01-2 2M7 9h8M7 13h8M7 17h5"/></svg>);
    case 'radio':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="12" cy="13" r="3"/><path {...p} d="M5.5 8.5a8 8 0 0113 0M8 11a4.5 4.5 0 017 0"/><rect {...p} x="3" y="14" width="18" height="6" rx="1"/></svg>);
    case 'person':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="12" cy="8" r="4"/><path {...p} d="M4 21a8 8 0 0116 0"/></svg>);
    case 'play':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} strokeWidth="1.2" fill={color} d="M7 5v14l12-7z"/></svg>);
    case 'pause':
      return (<svg viewBox="0 0 24 24" style={s}><rect {...p} strokeWidth="1.2" fill={color} x="6" y="5" width="4" height="14"/><rect {...p} strokeWidth="1.2" fill={color} x="14" y="5" width="4" height="14"/></svg>);
    case 'skip-back':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 5a7 7 0 107 7"/><path {...p} d="M12 2l-3 3 3 3"/><text x="12" y="15" textAnchor="middle" fontSize="7" fontFamily="system-ui" fontWeight="600" fill={color} stroke="none">15</text></svg>);
    case 'skip-fwd':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 5a7 7 0 117 7"/><path {...p} d="M12 2l3 3-3 3"/><text x="12" y="15" textAnchor="middle" fontSize="7" fontFamily="system-ui" fontWeight="600" fill={color} stroke="none">15</text></svg>);
    case 'chevron-right':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M9 6l6 6-6 6"/></svg>);
    case 'chevron-left':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M15 6l-6 6 6 6"/></svg>);
    case 'chevron-down':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M6 9l6 6 6-6"/></svg>);
    case 'search':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="11" cy="11" r="6"/><path {...p} d="M20 20l-4-4"/></svg>);
    case 'bookmark':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M6 4h12v17l-6-4-6 4z"/></svg>);
    case 'bookmark-filled':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} fill={color} strokeWidth="1.2" d="M6 4h12v17l-6-4-6 4z"/></svg>);
    case 'share':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="6" cy="12" r="2.5"/><circle {...p} cx="17" cy="6" r="2.5"/><circle {...p} cx="17" cy="18" r="2.5"/><path {...p} d="M8 11l7-4M8 13l7 4"/></svg>);
    case 'sun':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="12" cy="12" r="4"/><path {...p} d="M12 3v2M12 19v2M3 12h2M19 12h2M5.5 5.5l1.4 1.4M17.1 17.1l1.4 1.4M5.5 18.5l1.4-1.4M17.1 6.9l1.4-1.4"/></svg>);
    case 'moon':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M20 14.5A8 8 0 119.5 4a6.5 6.5 0 0010.5 10.5z"/></svg>);
    case 'building':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M5 21V5a1 1 0 011-1h12a1 1 0 011 1v16M9 8h2M13 8h2M9 12h2M13 12h2M9 16h2M13 16h2"/><path {...p} d="M2 21h20"/></svg>);
    case 'trending':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M3 17l6-6 4 4 8-8"/><path {...p} d="M14 7h7v7"/></svg>);
    case 'people':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="9" cy="8" r="3"/><path {...p} d="M3 20a6 6 0 0112 0"/><circle {...p} cx="17" cy="9" r="2.5"/><path {...p} d="M16 14a5 5 0 015 5"/></svg>);
    case 'palette':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 3a9 9 0 109 9c0-2-1.5-3-3-3h-2a2 2 0 010-4c1 0 1-1 1-2 0-0-2-0-5 0z"/><circle fill={color} stroke="none" cx="7.5" cy="12" r="1"/><circle fill={color} stroke="none" cx="9.5" cy="7.5" r="1"/><circle fill={color} stroke="none" cx="14" cy="7" r="1"/></svg>);
    case 'globe':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="12" cy="12" r="9"/><path {...p} d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/></svg>);
    case 'pin':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 21s-7-7-7-12a7 7 0 0114 0c0 5-7 12-7 12z"/><circle {...p} cx="12" cy="9" r="2.5"/></svg>);
    case 'trophy':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M8 4h8v5a4 4 0 01-8 0zM5 5h3v3a2 2 0 01-3 0zM19 5h-3v3a2 2 0 003 0zM9 13h6l-1 5h-4z"/><path {...p} d="M7 21h10"/></svg>);
    case 'chip':
      return (<svg viewBox="0 0 24 24" style={s}><rect {...p} x="6" y="6" width="12" height="12" rx="1"/><rect {...p} x="9" y="9" width="6" height="6"/><path {...p} d="M10 3v3M14 3v3M10 18v3M14 18v3M3 10h3M3 14h3M18 10h3M18 14h3"/></svg>);
    case 'check':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M5 12l5 5L20 7"/></svg>);
    case 'volume':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M4 9v6h4l5 4V5L8 9z"/><path {...p} d="M17 8c1.5 1 2 2.5 2 4s-0.5 3-2 4"/></svg>);
    case 'repeat':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M4 10V8a2 2 0 012-2h14l-3-3M20 14v2a2 2 0 01-2 2H4l3 3"/></svg>);
    case 'sparkle':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg>);
    case 'bell':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M6 15V10a6 6 0 0112 0v5l2 3H4z"/><path {...p} d="M10 20a2 2 0 004 0"/></svg>);
    case 'info':
      return (<svg viewBox="0 0 24 24" style={s}><circle {...p} cx="12" cy="12" r="9"/><path {...p} d="M12 11v5M12 8h.01"/></svg>);
    case 'type':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M4 7V5h16v2M9 5v14M15 5v14M7 19h4M13 19h4"/></svg>);
    case 'arrow-left':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M20 12H4M10 6l-6 6 6 6"/></svg>);
    case 'x':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M6 6l12 12M18 6L6 18"/></svg>);
    case 'dots':
      return (<svg viewBox="0 0 24 24" style={s}><circle fill={color} stroke="none" cx="5" cy="12" r="1.6"/><circle fill={color} stroke="none" cx="12" cy="12" r="1.6"/><circle fill={color} stroke="none" cx="19" cy="12" r="1.6"/></svg>);
    case 'sort':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M7 4v16M7 20l-3-3M7 20l3-3M17 20V4M17 4l-3 3M17 4l3 3"/></svg>);
    case 'list':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M8 6h12M8 12h12M8 18h12"/><circle fill={color} stroke="none" cx="4" cy="6" r="1.3"/><circle fill={color} stroke="none" cx="4" cy="12" r="1.3"/><circle fill={color} stroke="none" cx="4" cy="18" r="1.3"/></svg>);
    case 'track-prev':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} strokeWidth="1.2" fill={color} d="M19 5L9 12l10 7z"/><rect {...p} strokeWidth="1.2" fill={color} x="5" y="5" width="2" height="14"/></svg>);
    case 'track-next':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} strokeWidth="1.2" fill={color} d="M5 5l10 7-10 7z"/><rect {...p} strokeWidth="1.2" fill={color} x="17" y="5" width="2" height="14"/></svg>);
    case 'eye':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle {...p} cx="12" cy="12" r="3"/></svg>);
    case 'heart':
      return (<svg viewBox="0 0 24 24" style={s}><path {...p} d="M12 20s-7-4.5-7-10a4 4 0 017-2.5A4 4 0 0119 10c0 5.5-7 10-7 10z"/></svg>);
    default:
      return <svg viewBox="0 0 24 24" style={s}><rect {...p} x="4" y="4" width="16" height="16" rx="2"/></svg>;
  }
};

// ─── Brand logos for social login ───
// Rendered at fixed size inside a button; pass `color` to override (used by Apple on dark).
const BrandIcon = ({ name, size = 20, color }) => {
  const s = { width: size, height: size, flexShrink: 0 };
  switch (name) {
    case 'kakao':
      // Kakao speech bubble — simplified, renders as ink-on-yellow button
      return (
        <svg viewBox="0 0 24 24" style={s} fill={color || '#000'}>
          <path d="M12 3.5C6.75 3.5 2.5 6.9 2.5 11.1c0 2.7 1.8 5.1 4.5 6.4-.2.7-.7 2.6-.8 3-.1.5.2.5.4.4.2-.1 2.6-1.8 3.6-2.5.6.1 1.2.1 1.8.1 5.25 0 9.5-3.4 9.5-7.4s-4.25-7.6-9.5-7.6z"/>
        </svg>
      );
    case 'google':
      // Google "G" — official 4-color mark
      return (
        <svg viewBox="0 0 48 48" style={s}>
          <path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/>
          <path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/>
          <path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"/>
          <path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/>
        </svg>
      );
    case 'apple':
      // Apple logo — single-path silhouette
      return (
        <svg viewBox="0 0 24 24" style={s} fill={color || '#000'}>
          <path d="M17.05 12.54c-.03-2.75 2.25-4.07 2.35-4.14-1.28-1.87-3.27-2.13-3.98-2.16-1.69-.17-3.3.99-4.16.99-.86 0-2.2-.97-3.6-.94-1.85.03-3.56 1.08-4.51 2.73-1.92 3.33-.49 8.26 1.38 10.97.91 1.33 2 2.82 3.4 2.77 1.36-.05 1.88-.88 3.53-.88 1.64 0 2.12.88 3.57.85 1.47-.02 2.41-1.35 3.32-2.68 1.04-1.54 1.47-3.03 1.49-3.11-.03-.01-2.85-1.09-2.88-4.33zM14.31 4.68c.75-.91 1.25-2.17 1.12-3.43-1.08.04-2.39.72-3.16 1.62-.69.8-1.3 2.08-1.13 3.31 1.21.09 2.43-.61 3.17-1.5z"/>
        </svg>
      );
    default:
      return <svg viewBox="0 0 24 24" style={s}/>;
  }
};

window.Icon = Icon;
window.BrandIcon = BrandIcon;
