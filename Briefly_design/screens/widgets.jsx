// Homescreen widgets — podcast-player-centric
// The widget's main job: a glanceable play button for the current briefing.

// ─── Mini player — persistent bar shown above the tab bar when audio is playing
const MiniPlayer = ({ slot = 'AM', playing = true }) => {
  const eps = window.BRIEFLY.PODCAST_EPISODES;
  const cur = eps.find(e => e.slot === slot && e.date === '4. 18.') || eps[1];
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '8px 14px 8px 8px',
      background: 'var(--card)', borderTop: '1px solid var(--line)',
      flexShrink: 0, position: 'relative',
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'var(--line-soft)' }}>
        <div style={{ width: '38%', height: '100%', background: 'var(--accent)' }}/>
      </div>
      <div style={{
        width: 40, height: 40, background: 'var(--ink)', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column',
      }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 7.5, color: 'var(--paper)', opacity: 0.65, letterSpacing: '0.1em' }}>{cur.date}</div>
        <div style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 12, color: 'var(--paper)', lineHeight: 1, marginTop: 1 }}>{cur.slot}</div>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.08em' }}>● {cur.slotKo} 브리핑</div>
        <div style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, color: 'var(--ink)', lineHeight: 1.3, letterSpacing: '-0.01em', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
          {cur.subtitle}
        </div>
      </div>
      <button style={{ width: 36, height: 36, borderRadius: 999, background: 'var(--ink)', border: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
        {playing ? (
          <svg width="12" height="12" viewBox="0 0 12 12"><rect x="2" y="1.5" width="2.5" height="9" fill="var(--paper)"/><rect x="7.5" y="1.5" width="2.5" height="9" fill="var(--paper)"/></svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 12 12"><path d="M3 1.5v9l7-4.5z" fill="var(--paper)"/></svg>
        )}
      </button>
      <button style={{ background: 'none', border: 0, padding: 4, cursor: 'pointer', flexShrink: 0, display: 'flex' }}>
        <Icon name="x" size={14} color="var(--ink-3)"/>
      </button>
    </div>
  );
};

// ─── Waveform — simple decorative bars ───
const Waveform = ({ bars = 40, height = 24, color = '#1a1714', opacity = 0.35 }) => {
  // Stable pseudo-random heights (fixed seed via index math)
  const heights = Array.from({ length: bars }, (_, i) => {
    const v = Math.abs(Math.sin(i * 12.9898) * 43758.5453);
    return 0.25 + (v - Math.floor(v)) * 0.75;
  });
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 1.5, height, width: '100%' }}>
      {heights.map((h, i) => (
        <div key={i} style={{
          flex: 1, height: `${h * 100}%`,
          background: color, opacity: i < bars * 0.38 ? 1 : opacity,
          borderRadius: 0.5,
        }}/>
      ))}
    </div>
  );
};

// ─── iOS widgets — podcast player ───
// Small (2x2): cover art + big play button, date stamp
// Medium (4x2): horizontal player w/ waveform + skip controls
// Large (4x4): player + today's 3 topics list
const IOSWidget = ({ size = 'med' }) => {
  const cur = window.BRIEFLY.PODCAST_EPISODES.find(e => e.slot === 'AM' && e.date === '4. 18.');
  const topics = window.BRIEFLY.BRIEFING_AM.slice(0, 3);

  if (size === 'sm') {
    // 2x2 — pure player
    return (
      <div style={{
        width: 155, height: 155, borderRadius: 22, background: 'var(--ink)',
        padding: 14, boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Subtle inner paper frame */}
        <div style={{ position: 'absolute', inset: 8, border: '1px solid rgba(247,242,233,0.1)', borderRadius: 14, pointerEvents: 'none' }}/>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative' }}>
          <BrieflyMark size={12} color="var(--paper)"/>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'rgba(247,242,233,0.55)', letterSpacing: '0.1em' }}>{cur.date}</span>
        </div>
        <div style={{ position: 'relative' }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.14em', marginBottom: 3 }}>
            오전 · AM
          </div>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 800, color: 'var(--paper)', lineHeight: 1.2, letterSpacing: '-0.015em' }}>
            오늘의 브리핑
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, position: 'relative' }}>
          <button style={{
            width: 40, height: 40, borderRadius: 999, background: 'var(--paper)', border: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}>
            <svg width="14" height="14" viewBox="0 0 12 12"><path d="M3 1.5v9l7-4.5z" fill="var(--ink)"/></svg>
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'rgba(247,242,233,0.6)', letterSpacing: '0.06em' }}>
              6분 · 6개 토픽
            </div>
            <div style={{ marginTop: 4, height: 2, background: 'rgba(247,242,233,0.15)', borderRadius: 1 }}>
              <div style={{ width: '0%', height: '100%', background: 'var(--accent)' }}/>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (size === 'lg') {
    // 4x4 — player + topic list
    return (
      <div style={{
        width: 329, height: 329, borderRadius: 22, background: 'var(--paper)',
        padding: 16, boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 8, borderBottom: '2px solid var(--ink)' }}>
          <BrieflyMark size={14}/>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.1em' }}>{cur.date} · 오전</span>
        </div>
        {/* Player block */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, paddingTop: 12, paddingBottom: 12, borderBottom: '1px solid var(--line)' }}>
          <button style={{
            width: 48, height: 48, borderRadius: 999, background: 'var(--ink)', border: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <svg width="16" height="16" viewBox="0 0 12 12"><path d="M3 1.5v9l7-4.5z" fill="var(--paper)"/></svg>
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--ink)', lineHeight: 1.25, letterSpacing: '-0.01em' }}>
              오늘의 오전 브리핑
            </div>
            <div style={{ marginTop: 6, height: 18 }}>
              <Waveform bars={32} height={18}/>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.06em', marginTop: 2 }}>
              <span>0:00</span><span>6:12</span>
            </div>
          </div>
        </div>
        {/* Topics */}
        <div style={{ flex: 1, paddingTop: 10, display: 'flex', flexDirection: 'column', gap: 7 }}>
          {topics.map((t, i) => {
            const c = window.BRIEFLY.CAT_BY_ID[t.category];
            return (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: c.color, letterSpacing: '0.06em', flexShrink: 0, marginTop: 2, fontWeight: 700 }}>0{i+1}</span>
                <span style={{ fontFamily: 'var(--serif)', fontSize: 12, fontWeight: 600, lineHeight: 1.3, color: 'var(--ink)', letterSpacing: '-0.01em' }}>
                  {t.headline.length > 38 ? t.headline.slice(0, 36) + '…' : t.headline}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Medium 4x2 — horizontal podcast player
  return (
    <div style={{
      width: 329, height: 155, borderRadius: 22, background: 'var(--ink)',
      padding: 16, boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
      display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden',
    }}>
      <div style={{ position: 'absolute', inset: 10, border: '1px solid rgba(247,242,233,0.08)', borderRadius: 16, pointerEvents: 'none' }}/>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BrieflyMark size={13} color="var(--paper)"/>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.14em' }}>
            오전 브리핑
          </span>
        </div>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'rgba(247,242,233,0.55)', letterSpacing: '0.1em' }}>{cur.date}</span>
      </div>
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 14, position: 'relative' }}>
        <button style={{
          width: 54, height: 54, borderRadius: 999, background: 'var(--paper)', border: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          boxShadow: '0 3px 10px rgba(0,0,0,0.35)',
        }}>
          <svg width="18" height="18" viewBox="0 0 12 12"><path d="M3 1.5v9l7-4.5z" fill="var(--ink)"/></svg>
        </button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: 'var(--paper)', lineHeight: 1.25, letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {cur.subtitle}
          </div>
          <div style={{ marginTop: 6, height: 18, opacity: 0.95 }}>
            <Waveform bars={34} height={18} color="#f7f2e9" opacity={0.25}/>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--mono)', fontSize: 12, color: 'rgba(247,242,233,0.5)', letterSpacing: '0.06em', marginTop: 2 }}>
            <span>0:00</span>
            <span>{cur.duration}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Android widget — Material You podcast player ───
const AndroidWidget = () => {
  const cur = window.BRIEFLY.PODCAST_EPISODES.find(e => e.slot === 'AM' && e.date === '4. 18.');
  return (
    <div style={{
      width: 288, height: 120, borderRadius: 28, background: 'var(--paper)',
      padding: 14, boxShadow: '0 8px 20px rgba(0,0,0,0.15)',
      display: 'flex', alignItems: 'center', gap: 14,
      border: '1px solid var(--line)',
    }}>
      <button style={{
        width: 58, height: 58, borderRadius: 999, background: 'var(--accent)', border: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        boxShadow: '0 4px 10px rgba(160,58,40,0.35)',
      }}>
        <svg width="20" height="20" viewBox="0 0 12 12"><path d="M3.5 1.5v9l6.5-4.5z" fill="var(--paper)"/></svg>
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <BrieflyMark size={11}/>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.12em' }}>오전 · {cur.date}</span>
        </div>
        <div style={{ fontFamily: 'var(--serif)', fontSize: 13.5, fontWeight: 700, lineHeight: 1.25, color: 'var(--ink)', marginTop: 4, letterSpacing: '-0.01em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {cur.subtitle}
        </div>
        <div style={{ marginTop: 5, height: 14, opacity: 0.9 }}>
          <Waveform bars={28} height={14} color="#1a1714" opacity={0.3}/>
        </div>
      </div>
    </div>
  );
};

// ─── Homescreen mock frames ───
const IOSHomeMock = ({ children, label }) => (
  <div style={{
    width: 380, height: 580, borderRadius: 36, overflow: 'hidden',
    background: 'linear-gradient(180deg, #6b7a9a 0%, #3a4660 100%)',
    position: 'relative', padding: '30px 16px',
    boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
  }}>
    <div style={{ color: '#fff', textAlign: 'center', fontFamily: 'var(--sans)', fontSize: 12, letterSpacing: '0.08em', opacity: 0.8, marginBottom: 14 }}>{label}</div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
      {children}
    </div>
  </div>
);

const AndroidHomeMock = ({ children, label }) => (
  <div style={{
    width: 330, height: 300, borderRadius: 20, overflow: 'hidden',
    background: 'linear-gradient(180deg, #2b3a52 0%, #1a2236 100%)',
    position: 'relative', padding: '24px 18px',
    boxShadow: '0 20px 40px rgba(0,0,0,0.25)',
  }}>
    <div style={{ color: '#fff', textAlign: 'center', fontFamily: 'var(--sans)', fontSize: 12, letterSpacing: '0.08em', opacity: 0.8, marginBottom: 12 }}>{label}</div>
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      {children}
    </div>
  </div>
);

Object.assign(window, { MiniPlayer, IOSWidget, AndroidWidget, IOSHomeMock, AndroidHomeMock });
