// Today screen — AI curated briefing, editorial swipe cards
// Variants: A (stacked editorial card), B (full-bleed magazine), C (digest list)

const TodayScreen = ({ variant = 'A', slot = 'AM' }) => {
  const data = slot === 'AM' ? window.BRIEFLY.BRIEFING_AM : window.BRIEFLY.BRIEFING_PM;
  const active = 0;
  const topic = data[active];
  const cat = window.BRIEFLY.CAT_BY_ID[topic.category];

  const Header = (
    <div style={{ padding: '14px 24px 10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '2px solid var(--ink)', paddingBottom: 10 }}>
        <BrieflyMark size={18}/>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.08em', color: 'var(--ink-3)' }}>{window.BRIEFLY.todayKorean}</span>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: 14 }}>
        <div>
          <h1 style={{ fontFamily: 'var(--serif)', fontSize: 32, fontWeight: 900, letterSpacing: '-0.03em' }}>오늘의 브리핑</h1>
        </div>
        {/* AM/PM toggle */}
        <div style={{ display: 'inline-flex', background: 'var(--paper-2)', borderRadius: 999, padding: 3, border: '1px solid var(--line)' }}>
          {['AM', 'PM'].map(s => (
            <span key={s} style={{
              minHeight: 36, minWidth: 56, padding: '8px 16px', borderRadius: 999, fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.04em',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              background: s === slot ? 'var(--ink)' : 'transparent',
              color: s === slot ? 'var(--paper)' : 'var(--ink-3)',
            }}>{s === 'AM' ? '오전' : '오후'}</span>
          ))}
        </div>
      </div>
    </div>
  );

  const Indicator = (
    <div style={{ display: 'flex', gap: 4, padding: '8px 24px 14px' }}>
      {data.map((_, i) => (
        <div key={i} style={{
          flex: 1, height: 3, borderRadius: 2,
          background: i === active ? 'var(--ink)' : 'var(--line)',
        }}/>
      ))}
    </div>
  );

  if (variant === 'A') {
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        {Header}
        {Indicator}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 20px 16px' }}>
          <div style={{ background: 'var(--card)', borderRadius: 4, border: '1px solid var(--line)', boxShadow: '0 6px 20px rgba(40,30,20,0.06)', overflow: 'hidden' }}>
            <div style={{ padding: '18px 22px 14px', borderBottom: '1px solid var(--line-soft)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <CatBadge cat={topic.category} size="md"/>
                <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em' }}>토픽 {String(active+1).padStart(2,'0')} / {String(data.length).padStart(2,'0')}</span>
              </div>
              <h2 style={{ fontFamily: 'var(--serif)', fontSize: 26, fontWeight: 800, marginTop: 16, lineHeight: 1.2, letterSpacing: '-0.02em' }}>
                {topic.headline}
              </h2>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
                {topic.keywords.map(k => (
                  <span key={k} style={{ fontFamily: 'var(--sans)', fontSize: 13, color: cat.color, border: `1px solid ${cat.color}33`, padding: '6px 10px', borderRadius: 2, background: `${cat.color}0d`, minHeight: 32, display: 'inline-flex', alignItems: 'center' }}>#{k}</span>
                ))}
              </div>
            </div>
            <Placeholder h={170} label="대표 사진" cat={topic.category} radius={0}/>
            <div style={{ padding: '16px 22px 20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <Icon name="sparkle" size={14} color="var(--accent)"/>
                <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.06em' }}>AI 요약</span>
              </div>
              <p style={{ fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink)', lineHeight: 1.75 }}>
                {topic.summary}
              </p>
              <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--line-soft)' }}>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginBottom: 8, letterSpacing: '0.04em' }}>대표 기사</div>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 600, color: 'var(--ink-2)', lineHeight: 1.5 }}>"{topic.representative_title}"</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)', marginTop: 8 }}>
                  {topic.representative_press} · 관련 기사 <b style={{ color: 'var(--accent)' }}>{topic.cluster_size}건</b>
                </div>
              </div>
            </div>
            <div style={{ padding: '0 22px 18px' }}>
              <button style={{ width: '100%', minHeight: 48, padding: '14px', background: 'transparent', color: 'var(--ink)', border: '1px solid var(--ink)', borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                이 토픽 자세히 보기 <Icon name="chevron-right" size={16}/>
              </button>
            </div>
          </div>
          {/* Next preview */}
          <div style={{ marginTop: 16, padding: '12px 16px', opacity: 0.5, fontFamily: 'var(--serif)', fontSize: 15, color: 'var(--ink-2)', lineHeight: 1.5 }}>
            다음 → <b>{data[1].headline}</b>
          </div>
        </div>
        <TabBar active="today"/>
        <HomeIndicator/>
      </div>
    );
  }

  if (variant === 'B') {
    // Full-bleed magazine cover — documentary photo + warm gray overlay
    // Placeholder: textured dark gradient imitating a desaturated press photo.
    // In production this is replaced by the topic's hero image, always
    // desaturated to keep type legible regardless of source photography.
    const photoBg = `
      radial-gradient(ellipse at 30% 20%, rgba(180,160,135,0.35) 0%, transparent 55%),
      radial-gradient(ellipse at 75% 75%, rgba(90,70,55,0.4) 0%, transparent 60%),
      linear-gradient(180deg, #3a3530 0%, #241f1b 50%, #1a1714 100%)
    `;
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: '#1a1714', display: 'flex', flexDirection: 'column', position: 'relative' }}>
        {/* Photo background layer */}
        <div style={{ position: 'absolute', inset: 0, background: photoBg, filter: 'grayscale(0.55) contrast(0.95)' }}/>
        {/* Subtle paper grain / ink overlay */}
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(26,23,20,0.2) 0%, rgba(26,23,20,0.55) 60%, rgba(26,23,20,0.85) 100%)' }}/>

        <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <StatusBarLite dark/>
          <div style={{ padding: '14px 24px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <BrieflyMark size={18} color="var(--paper)"/>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'rgba(247,242,233,0.7)', letterSpacing: '0.04em' }}>{window.BRIEFLY.todayKorean} · {slot === 'AM' ? '오전' : '오후'}</span>
          </div>
          <div style={{ padding: '0 24px 8px' }}>
            <div style={{ display: 'flex', gap: 4 }}>
              {data.map((_, i) => (
                <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i === active ? 'var(--paper)' : 'rgba(247,242,233,0.3)' }}/>
              ))}
            </div>
          </div>
          <div style={{ flex: 1, padding: '30px 28px 20px', color: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ display: 'inline-block', width: 8, height: 8, background: cat.color, borderRadius: 999 }}/>
              <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'rgba(247,242,233,0.85)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
                {cat.ko} · 관련 기사 {topic.cluster_size}건
              </span>
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 120, fontWeight: 400, opacity: 0.22, lineHeight: 1, marginTop: 10, letterSpacing: '-0.05em' }}>
              0{active+1}
            </div>
            <h2 style={{ fontFamily: 'var(--serif)', fontSize: 36, fontWeight: 900, lineHeight: 1.08, letterSpacing: '-0.03em', marginTop: -38, textShadow: '0 2px 12px rgba(0,0,0,0.35)' }}>
              {topic.headline}
            </h2>
            <div style={{ flex: 1 }}/>
            <p style={{ fontFamily: 'var(--serif)', fontSize: 16, lineHeight: 1.7, opacity: 0.95, borderLeft: '2px solid var(--paper)', paddingLeft: 12 }}>
              {topic.summary}
            </p>
            <div style={{ display: 'flex', gap: 10, marginTop: 18, alignItems: 'center' }}>
              <button style={{ flex: 1, minHeight: 48, padding: '14px', background: 'var(--paper)', color: 'var(--ink)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
                자세히 보기
              </button>
              <button style={{ width: 48, height: 48, background: 'rgba(247,242,233,0.12)', border: '1px solid rgba(247,242,233,0.3)', color: 'var(--paper)', borderRadius: 2, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(6px)' }}>
                <Icon name="bookmark" size={18} color="var(--paper)"/>
              </button>
            </div>
          </div>
          <div style={{ background: 'var(--paper)' }}>
            <TabBar active="today"/>
            <HomeIndicator/>
          </div>
        </div>
      </div>
    );
  }

  // C — digest index (all 6 visible, scroll through)
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      {Header}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ padding: '4px 24px 10px', fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em' }}>
          오늘의 여섯 가지 이슈
        </div>
        {data.map((t, i) => {
          const c = window.BRIEFLY.CAT_BY_ID[t.category];
          return (
            <div key={t.topic_id} style={{ padding: '18px 24px', borderTop: i === 0 ? '2px solid var(--ink)' : '1px solid var(--line-soft)' }}>
              <div style={{ display: 'flex', gap: 14 }}>
                <div style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 40, color: c.color, lineHeight: 0.9, opacity: 0.9, flexShrink: 0, width: 48 }}>
                  0{i+1}
                </div>
                <div style={{ flex: 1 }}>
                  <CatBadge cat={t.category}/>
                  <h3 style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 700, lineHeight: 1.3, marginTop: 8, letterSpacing: '-0.015em' }}>{t.headline}</h3>
                  <p style={{ fontFamily: 'var(--sans)', fontSize: 15, color: 'var(--ink-2)', marginTop: 8, lineHeight: 1.7 }}>
                    {t.summary.slice(0, 80)}…
                  </p>
                  <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 8, letterSpacing: '0.04em' }}>
                    관련 기사 {t.cluster_size}건 · {t.representative_press}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <TabBar active="today"/>
      <HomeIndicator/>
    </div>
  );
};

window.TodayScreen = TodayScreen;
