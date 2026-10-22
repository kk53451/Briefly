// Search screen — discovery

const SearchScreen = ({ state = 'initial' }) => {
  const recent = ['금리 인상', '전세사기 특별법', '칸 영화제', '삼성 2나노', 'GPT-6'];
  const trending = [
    { rank: 1, kw: '기준금리 3.75%', delta: 'up', cat: 'economy' },
    { rank: 2, kw: '추경 35조', delta: 'up', cat: 'politics' },
    { rank: 3, kw: '美 CPI 2.4%', delta: 'same', cat: 'world' },
    { rank: 4, kw: '칸 영화제', delta: 'up', cat: 'culture' },
    { rank: 5, kw: '전세사기 특별법', delta: 'down', cat: 'society' },
    { rank: 6, kw: '삼성 2나노', delta: 'same', cat: 'tech' },
    { rank: 7, kw: 'GPT-6', delta: 'up', cat: 'tech' },
    { rank: 8, kw: '원·달러 1,315원', delta: 'down', cat: 'economy' },
  ];
  const results = [
    { title: '한국은행, 기준금리 3.75%로 0.25%p 인상…물가 둔화 더뎌', provider: '연합뉴스', cat: 'economy', time: '06:10', cluster: 47 },
    { title: '주담대 변동금리, 다음 주부터 0.2%p 오른다', provider: 'KBS', cat: 'economy', time: '08:30', cluster: 14 },
    { title: '美 CPI 2.4% 둔화…6월 금리인하 확률 72%', provider: '매일경제', cat: 'world', time: '06:30', cluster: 28 },
    { title: '원·달러 환율 1,315원…3주 만에 최저치', provider: '매일경제', cat: 'economy', time: '07:42', cluster: 22 },
  ];

  const showResults = state === 'results';
  const query = showResults ? '금리' : '';

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      {/* Search bar */}
      <div style={{ padding: '10px 16px 12px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: '2px solid var(--ink)' }}>
        <button style={{ background: 'none', border: 0, padding: 4, cursor: 'pointer', display: 'flex' }}>
          <Icon name="arrow-left" size={22}/>
        </button>
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, background: 'var(--paper-2)', border: '1px solid var(--line)', borderRadius: 2, padding: '12px 14px', minHeight: 48 }}>
          <Icon name="search" size={18} color="var(--ink-3)"/>
          <input readOnly value={query} placeholder="헤드라인, 키워드, 주제 검색"
            style={{ flex: 1, background: 'transparent', border: 0, outline: 'none', fontFamily: 'var(--sans)', fontSize: 16, color: 'var(--ink)' }}/>
          {showResults && <Icon name="x" size={16} color="var(--ink-3)"/>}
        </div>
      </div>

      {!showResults && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          {/* Recent searches */}
          <div style={{ padding: '18px 24px 6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
              <span style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, color: 'var(--ink-2)' }}>최근 검색</span>
              <span style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)', minHeight: 32, padding: '6px 4px', display: 'inline-flex', alignItems: 'center' }}>전체 삭제</span>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {recent.map(r => (
                <span key={r} style={{ padding: '8px 14px', background: 'var(--paper-2)', border: '1px solid var(--line)', borderRadius: 999, fontFamily: 'var(--sans)', fontSize: 14, color: 'var(--ink-2)', display: 'inline-flex', alignItems: 'center', gap: 6, minHeight: 36 }}>
                  <Icon name="clock" size={12} color="var(--ink-3)"/>{r}
                </span>
              ))}
            </div>
          </div>

          {/* Trending */}
          <div style={{ padding: '22px 24px 10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
              <div>
                <span style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em' }}>실시간 많이 찾는</span>
              </div>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>07:22 기준</span>
            </div>
            {trending.map((t, i) => {
              const c = window.BRIEFLY.CAT_BY_ID[t.cat];
              const deltaSym = { up: '▲', down: '▼', same: '·' }[t.delta];
              const deltaCol = { up: '#b54a3a', down: '#3d6b8c', same: 'var(--ink-4)' }[t.delta];
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 0', borderBottom: i < trending.length - 1 ? '1px solid var(--line-soft)' : 'none' }}>
                  <div style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 900, color: t.rank <= 3 ? 'var(--accent)' : 'var(--ink-4)', width: 22, lineHeight: 1 }}>
                    {t.rank}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 600, color: 'var(--ink)', letterSpacing: '-0.01em' }}>{t.kw}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                      <span className="cat-dot" style={{ background: c.color }}/>
                      <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>{c.ko}</span>
                    </div>
                  </div>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 13, color: deltaCol, fontWeight: 600, letterSpacing: '0.04em' }}>
                    {deltaSym}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {showResults && (
        <div style={{ flex: 1, overflow: 'auto' }}>
          <div style={{ padding: '14px 24px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 14, color: 'var(--ink-2)' }}>
              "<b>금리</b>" 검색 결과 <b style={{ color: 'var(--accent)' }}>{results.length}건</b>
            </span>
            <span style={{ fontFamily: 'var(--label)', fontSize: 13, color: 'var(--ink-3)', minHeight: 32, padding: '6px 8px', display: 'inline-flex', alignItems: 'center' }}>최신순 ▾</span>
          </div>
          {/* Filter chips */}
          <div style={{ padding: '0 24px 12px', display: 'flex', gap: 6, overflowX: 'auto' }}>
            {['전체', '기사', '토픽', '팟캐스트'].map((f, i) => (
              <span key={f} style={{
                padding: '8px 14px', fontFamily: 'var(--sans)', fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', minHeight: 36, display: 'inline-flex', alignItems: 'center',
                border: `1px solid ${i === 0 ? 'var(--ink)' : 'var(--line)'}`, borderRadius: 999,
                background: i === 0 ? 'var(--ink)' : 'transparent',
                color: i === 0 ? 'var(--paper)' : 'var(--ink-2)',
              }}>{f}</span>
            ))}
          </div>
          <div style={{ padding: '0 24px 16px' }}>
            {results.map((r, i) => (
              <div key={i} style={{ padding: '14px 0', borderTop: i === 0 ? '1px solid var(--line)' : '1px solid var(--line-soft)' }}>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 6 }}>
                  <CatBadge cat={r.cat}/>
                  <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>· {r.provider} · {r.time}</span>
                </div>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700, lineHeight: 1.4, letterSpacing: '-0.01em' }}
                  dangerouslySetInnerHTML={{ __html: r.title.replace(/금리/g, '<mark style="background:#f3e3b8;color:#1a1714;padding:0 2px">금리</mark>') }}/>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 8 }}>
                  관련 기사 {r.cluster}건
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <HomeIndicator/>
    </div>
  );
};

window.SearchScreen = SearchScreen;
