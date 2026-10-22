// Shared UI primitives for Briefly screens
// Width: 390 (iPhone), Height: 844 (iOS content area excl. status bar)

const StatusBarLite = ({ dark }) => {
  const c = dark ? '#fff' : 'var(--ink)';
  return (
    <div style={{
      height: 44, display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 22px',
      fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 600, color: c,
      flexShrink: 0,
    }}>
      <span>9:41</span>
      <span style={{ display: 'flex', gap: 6, alignItems: 'center', opacity: 0.9 }}>
        <svg width="17" height="11" viewBox="0 0 17 11"><path fill={c} d="M2 7h2v3H2zM6 5h2v5H6zM10 3h2v7h-2zM14 1h2v9h-2z"/></svg>
        <svg width="16" height="11" viewBox="0 0 16 11"><path fill={c} d="M8 2a9 9 0 017 3l-1 1a8 8 0 00-12 0l-1-1a9 9 0 016-3z M8 5a6 6 0 014 2l-1 1a5 5 0 00-6 0l-1-1a6 6 0 014-2zM8 8a3 3 0 012 1l-2 2-2-2a3 3 0 012-1z"/></svg>
        <svg width="24" height="11" viewBox="0 0 24 11"><rect fill="none" stroke={c} strokeWidth="0.7" opacity="0.4" x="0.5" y="0.5" width="21" height="10" rx="2"/><rect fill={c} x="2" y="2" width="17" height="7" rx="1"/><rect fill={c} opacity="0.4" x="22" y="3.5" width="1.5" height="4" rx="0.5"/></svg>
      </span>
    </div>
  );
};

const HomeIndicator = () => (
  <div style={{
    height: 34, display: 'flex', justifyContent: 'center', alignItems: 'flex-end',
    paddingBottom: 8, flexShrink: 0,
  }}>
    <div style={{ width: 134, height: 5, borderRadius: 100, background: 'rgba(0,0,0,0.35)' }} />
  </div>
);

// Category pill (badge)
const CatBadge = ({ cat, size = 'sm' }) => {
  const c = window.BRIEFLY.CAT_BY_ID[cat];
  const small = size === 'sm';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      fontFamily: 'var(--sans)', fontSize: small ? 10 : 12, fontWeight: 600,
      letterSpacing: '0.06em', color: c.color,
      textTransform: 'uppercase',
    }}>
      <span style={{ width: small ? 5 : 7, height: small ? 5 : 7, borderRadius: 999, background: c.color }}/>
      {c.ko}
    </span>
  );
};

// Striped placeholder image, editorial style
const Placeholder = ({ w = '100%', h = 160, label, cat = 'economy', radius = 2 }) => {
  const c = window.BRIEFLY.CAT_BY_ID[cat]?.color || '#8a7b65';
  return (
    <div style={{
      width: w, height: h, background: `repeating-linear-gradient(135deg, ${c}22 0 8px, ${c}11 8px 16px)`,
      borderRadius: radius, position: 'relative', overflow: 'hidden',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      border: `1px solid ${c}33`,
    }}>
      <div style={{
        fontFamily: 'var(--mono)', fontSize: 12, color: c,
        letterSpacing: '0.08em', textTransform: 'uppercase', opacity: 0.8,
      }}>{label || 'photo'}</div>
    </div>
  );
};

// Tab bar (bottom nav)
const TabBar = ({ active = 'today', onTab }) => {
  const items = [
    { id: 'home', label: '홈', icon: 'home' },
    { id: 'today', label: '투데이', icon: 'newspaper' },
    { id: 'podcast', label: '팟캐스트', icon: 'radio' },
    { id: 'profile', label: '프로필', icon: 'person' },
  ];
  return (
    <div style={{
      borderTop: '1px solid var(--line)',
      background: 'var(--card)',
      display: 'flex', padding: '8px 0 4px', flexShrink: 0,
    }}>
      {items.map(it => {
        const a = it.id === active;
        return (
          <button key={it.id} onClick={() => onTab && onTab(it.id)} style={{
            flex: 1, background: 'none', border: 0, padding: '6px 0',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
            color: a ? 'var(--ink)' : 'var(--ink-3)', cursor: 'pointer',
          }}>
            <Icon name={it.icon} size={22} strokeWidth={a ? 1.8 : 1.4}/>
            <span style={{ fontSize: 12, fontWeight: a ? 700 : 500, letterSpacing: '0.02em' }}>{it.label}</span>
          </button>
        );
      })}
    </div>
  );
};

// Thin masthead wordmark
const BrieflyMark = ({ size = 18, color = 'var(--ink)' }) => (
  <span style={{
    fontFamily: 'var(--serif)', fontWeight: 700, fontSize: size,
    letterSpacing: '-0.02em', color,
  }}>
    Briefly<span style={{ color: 'var(--accent)' }}>.</span>
  </span>
);

Object.assign(window, { StatusBarLite, HomeIndicator, CatBadge, Placeholder, TabBar, BrieflyMark });
