// Onboarding — category selection

const OnboardingScreen = ({ variant = 'A' }) => {
  const cats = window.BRIEFLY.CATEGORIES;
  const selected = { economy: true, politics: true, world: true, tech: true };

  if (variant === 'A') {
    // 2-column soft cards with muted accent on select
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        <div style={{ padding: '14px 24px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--ink)' }}>
          <button style={{ background: 'none', border: 0, padding: 0, color: 'var(--ink-3)', cursor: 'pointer' }}>
            <Icon name="arrow-left" size={22}/>
          </button>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.15em', color: 'var(--ink-3)' }}>2 / 2</span>
        </div>
        <div style={{ padding: '16px 24px 8px' }}>
          <h1 style={{ fontFamily: 'var(--serif)', fontSize: 30, fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.02em' }}>
            어떤 소식을<br/>전해드릴까요?
          </h1>
          <p style={{ fontFamily: 'var(--sans)', fontSize: 16, color: 'var(--ink-2)', marginTop: 12, lineHeight: 1.65 }}>
            선택한 주제 중심으로 오늘의 브리핑과 팟캐스트를 준비합니다.
          </p>
        </div>
        <div style={{ flex: 1, overflow: 'hidden', padding: '16px 20px 12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gridAutoRows: '1fr', gap: 10, height: '100%' }}>
            {cats.map(c => {
              const sel = selected[c.id];
              return (
                <div key={c.id} style={{
                  borderRadius: 4,
                  background: sel ? c.color : 'var(--card)',
                  border: `1px solid ${sel ? c.color : 'var(--line)'}`,
                  padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 12,
                  position: 'relative',
                  boxShadow: sel ? '0 2px 10px rgba(0,0,0,0.08)' : '0 1px 2px rgba(0,0,0,0.03)',
                }}>
                  <Icon name={c.icon} size={24} color={sel ? 'var(--paper)' : c.color} strokeWidth={1.5}/>
                  <div style={{ fontFamily: 'var(--serif)', fontSize: 20, fontWeight: 700, color: sel ? 'var(--paper)' : 'var(--ink)', letterSpacing: '-0.01em', flex: 1 }}>{c.ko}</div>
                  {sel && (
                    <div style={{ width: 20, height: 20, borderRadius: 999, background: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Icon name="check" size={13} color={c.color} strokeWidth={2.6}/>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <div style={{ padding: '12px 24px 12px', borderTop: '1px solid var(--line)', background: 'var(--card)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 14, color: 'var(--ink-2)' }}>
              <b style={{ color: 'var(--accent)' }}>4개</b> 선택됨
            </span>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)' }}>최소 1개 이상</span>
          </div>
          <button style={{ width: '100%', minHeight: 48, padding: '16px', background: 'var(--ink)', color: 'var(--paper)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>
            시작하기
          </button>
        </div>
        <HomeIndicator/>
      </div>
    );
  }

  // B — list with checkable rows (editorial index)
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--ink)' }}>
        <button style={{ background: 'none', border: 0, padding: 0, color: 'var(--ink-3)', cursor: 'pointer' }}>
          <Icon name="arrow-left" size={22}/>
        </button>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.15em', color: 'var(--ink-3)' }}>2 / 2</span>
      </div>
      <div style={{ padding: '16px 24px 20px' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: 28, fontWeight: 700, lineHeight: 1.15 }}>
          매일 받아볼 주제를<br/>골라주세요.
        </h1>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '0 24px', borderTop: '1px solid var(--ink)', borderBottom: '1px solid var(--line)' }}>
        {cats.map((c, i) => {
          const sel = selected[c.id];
          return (
            <div key={c.id} style={{
              display: 'flex', alignItems: 'center', gap: 16,
              padding: '16px 0',
              borderBottom: i < cats.length - 1 ? '1px solid var(--line-soft)' : 'none',
            }}>
              <div style={{
                width: 22, height: 22, borderRadius: 4,
                border: `1.5px solid ${sel ? c.color : 'var(--line)'}`,
                background: sel ? c.color : 'transparent',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {sel && <Icon name="check" size={14} color="var(--paper)" strokeWidth={2.4}/>}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 20, fontWeight: 700, color: 'var(--ink)' }}>{c.ko}</div>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 6 }}>
                  하루 약 {8 + i * 2}건 큐레이션
                </div>
              </div>
              <Icon name={c.icon} size={22} color={sel ? c.color : 'var(--ink-4)'} strokeWidth={1.4}/>
            </div>
          );
        })}
      </div>
      <div style={{ padding: '16px 24px 12px', background: 'var(--card)' }}>
        <button style={{ width: '100%', minHeight: 48, padding: '16px', background: 'var(--accent)', color: 'var(--paper)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>
          4개 주제로 시작하기
        </button>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.OnboardingScreen = OnboardingScreen;
