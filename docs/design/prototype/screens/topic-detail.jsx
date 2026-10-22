// Topic detail — deep dive on a Today briefing topic (news cluster)

const TopicDetailScreen = () => {
  const topic = window.BRIEFLY.BRIEFING_AM[0]; // 금리 인상
  const cat = window.BRIEFLY.CAT_BY_ID[topic.category];

  const timeline = [
    { time: '06:10', source: '연합뉴스', label: '최초 보도', title: '한국은행, 기준금리 3.75%로 0.25%p 인상' },
    { time: '06:24', source: 'KBS', label: '속보', title: '한은 "근원물가 둔화 더디다" 긴급 회견' },
    { time: '07:05', source: '매일경제', label: '시장 반응', title: '원·달러 환율 1,315원…3주 만 최저치' },
    { time: '07:42', source: '한겨레', label: '분석', title: '가계부채 후폭풍…추가 인상 가능성은?' },
    { time: '09:15', source: '한국경제', label: '증시 반응', title: '코스피 3,100 회복…반도체·2차전지 동반 상승' },
    { time: '10:45', source: '조선비즈', label: '관련', title: '주담대 변동금리, 다음 주부터 0.2%p 오른다' },
  ];
  const perspectives = [
    { press: '연합뉴스', stance: '중립', note: '사실 관계 중심 — 결정 과정과 수치' },
    { press: '한겨레', stance: '비판', note: '가계부채 부담 · 서민경제 영향 조명' },
    { press: '매일경제', stance: '시장중심', note: '외환·증시·채권 반응 집중 분석' },
  ];

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Icon name="arrow-left" size={22}/>
        <div style={{ display: 'flex', gap: 18 }}>
          <Icon name="bookmark" size={20} color="var(--ink-3)"/>
          <Icon name="share" size={20} color="var(--ink-3)"/>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Hero */}
        <div style={{ padding: '6px 24px 20px', borderBottom: `2px solid ${cat.color}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <CatBadge cat={topic.category} size="md"/>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>· 토픽 01 / 06</span>
          </div>
          <h1 style={{ fontFamily: 'var(--serif)', fontSize: 28, fontWeight: 900, lineHeight: 1.18, letterSpacing: '-0.025em' }}>
            {topic.headline}
          </h1>
          <div style={{ display: 'flex', gap: 14, marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--line-soft)' }}>
            {[
              ['47', '관련 기사'],
              ['12', '언론사'],
              ['6h', '보도 기간'],
            ].map(([v, l], i) => (
              <div key={i} style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 900, color: 'var(--ink)', letterSpacing: '-0.02em' }}>{v}</div>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em', marginTop: 4 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* AI summary */}
        <div style={{ padding: '18px 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
            <Icon name="sparkle" size={14} color="var(--accent)"/>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.1em' }}>한눈에 보기</span>
          </div>
          <p style={{ fontFamily: 'var(--serif)', fontSize: 16, lineHeight: 1.75 }}>{topic.summary}</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
            {topic.keywords.map(k => (
              <span key={k} style={{ fontFamily: 'var(--sans)', fontSize: 13, color: cat.color, border: `1px solid ${cat.color}55`, padding: '6px 10px', borderRadius: 2, background: `${cat.color}0d`, minHeight: 32, display: 'inline-flex', alignItems: 'center' }}>#{k}</span>
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div style={{ padding: '6px 24px 16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 8, borderBottom: '1px solid var(--line)', marginBottom: 4 }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em' }}>오늘의 타임라인</span>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em' }}>{timeline.length}건</span>
          </div>
          {timeline.map((t, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: i < timeline.length - 1 ? '1px solid var(--line-soft)' : 'none', position: 'relative' }}>
              <div style={{ width: 52, flexShrink: 0, position: 'relative' }}>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 13, fontWeight: 600, color: 'var(--ink)', letterSpacing: '0.04em' }}>{t.time}</div>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4 }}>{t.source}</div>
                {i < timeline.length - 1 && <div style={{ position: 'absolute', left: 4, top: 28, bottom: -12, width: 1, background: 'var(--line)' }}/>}
                <div style={{ position: 'absolute', left: 1, top: 6, width: 7, height: 7, borderRadius: 999, background: i === 0 ? 'var(--accent)' : 'var(--ink-4)', border: `2px solid var(--paper)` }}/>
              </div>
              <div style={{ flex: 1, paddingLeft: 8 }}>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: cat.color, letterSpacing: '0.08em', background: `${cat.color}15`, padding: '3px 8px', borderRadius: 2 }}>{t.label}</span>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 600, color: 'var(--ink)', marginTop: 8, lineHeight: 1.5, letterSpacing: '-0.01em' }}>{t.title}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Perspectives — 다른 시각 */}
        <div style={{ padding: '6px 24px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 8, borderBottom: '1px solid var(--line)', marginBottom: 4 }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em' }}>다른 시각</span>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em' }}>3개 언론사</span>
          </div>
          {perspectives.map((p, i) => (
            <div key={i} style={{ padding: '12px 0', borderBottom: i < perspectives.length - 1 ? '1px solid var(--line-soft)' : 'none' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700 }}>{p.press}</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--paper)', background: 'var(--ink)', padding: '3px 8px', letterSpacing: '0.06em' }}>{p.stance}</span>
              </div>
              <div style={{ fontFamily: 'var(--sans)', fontSize: 15, color: 'var(--ink-2)', marginTop: 8, lineHeight: 1.6 }}>{p.note}</div>
            </div>
          ))}
        </div>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.TopicDetailScreen = TopicDetailScreen;
