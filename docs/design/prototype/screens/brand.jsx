// App icon & Splash — A4 wordmark only, Splash A only

// ─── App Icon frame ───
const IconFrame = ({ size = 180, bg = 'var(--paper)', children }) => (
  <div style={{
    width: size, height: size, borderRadius: size * 0.22, background: bg,
    boxShadow: '0 12px 30px rgba(0,0,0,0.18), 0 0 0 1px rgba(0,0,0,0.06)',
    overflow: 'hidden', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  }}>
    {children}
  </div>
);

// Icon — "Briefly." full wordmark (A4, final)
const IconAWord = ({ size = 180, bg = '#f7f2e9', ink = '#1a1714', dot = '#a03a28' }) => (
  <IconFrame size={size} bg={bg}>
    <div style={{
      fontFamily: 'var(--serif)', fontWeight: 900, fontSize: size * 0.24,
      letterSpacing: '-0.04em', color: ink, lineHeight: 1,
    }}>
      Briefly<span style={{ color: dot }}>.</span>
    </div>
  </IconFrame>
);

// ─── App Icon Card ───
const IconCard = ({ label, children, subtitle }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
    {children}
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, color: 'var(--ink)' }}>{label}</div>
      {subtitle && <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.08em', marginTop: 3 }}>{subtitle}</div>}
    </div>
  </div>
);

// ─── Home screen mock with Briefly icon placed on iOS-style grid ───
const HomeScreenPreview = ({ IconComp }) => {
  const apps = [
    { name: 'Messages', bg: '#5BC249', icon: '💬' },
    { name: 'Calendar', bg: '#FFFFFF', icon: '📅' },
    { name: 'Photos', bg: 'linear-gradient(135deg, #FFB84D, #FF5A8A, #6B6BFF)', icon: '🖼' },
    { name: 'Camera', bg: '#2A2A2A', icon: '📷' },
  ];
  return (
    <div style={{
      width: 260, borderRadius: 22, overflow: 'hidden',
      background: 'linear-gradient(180deg, #4a5c7c 0%, #2b3a52 100%)',
      padding: '40px 20px 14px', boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
    }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 18, placeItems: 'center' }}>
        {apps.slice(0, 3).map((a, i) => (
          <div key={i} style={{ textAlign: 'center' }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: a.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>{a.icon}</div>
            <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: '#fff', marginTop: 4 }}>{a.name}</div>
          </div>
        ))}
        <div style={{ textAlign: 'center' }}>
          <IconComp size={44}/>
          <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: '#fff', marginTop: 4, fontWeight: 600 }}>Briefly</div>
        </div>
        {apps.slice(3).map((a, i) => (
          <div key={i + 100} style={{ textAlign: 'center' }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: a.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20 }}>{a.icon}</div>
            <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: '#fff', marginTop: 4 }}>{a.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ─── Splash A — Masthead (신문 1면 스타일), 정렬 보정판 ───
// 390×844 full-bleed; uses safe flex regions so nothing clips.
const SplashA = () => (
  <div style={{
    width: '100%', height: '100%', background: 'var(--paper)',
    display: 'flex', flexDirection: 'column', position: 'relative',
  }}>
    <StatusBarLite/>
    {/* Center — wordmark + tagline, truly centered in remaining space */}
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      justifyContent: 'center', alignItems: 'center', padding: '0 32px',
    }}>
      <div style={{
        fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 76,
        letterSpacing: '-0.04em', color: 'var(--ink)', lineHeight: 0.9,
      }}>
        Briefly<span style={{ color: 'var(--accent)' }}>.</span>
      </div>
      <div style={{ width: 40, height: 1, background: 'var(--ink-3)', margin: '24px 0', opacity: 0.5 }}/>
      <div style={{
        fontFamily: 'var(--serif)', fontSize: 15,
        color: 'var(--ink-2)', textAlign: 'center', letterSpacing: '-0.01em', lineHeight: 1.5,
        wordBreak: 'keep-all',
      }}>
        목소리로 편하게 듣는<br/>오늘의 헤드라인
      </div>
    </div>

    {/* Footer — breathing room above home indicator */}
    <div style={{ paddingBottom: 28 }}/>
  </div>
);

window.IconAWord = IconAWord;
window.IconCard = IconCard;
window.HomeScreenPreview = HomeScreenPreview;
window.SplashA = SplashA;
