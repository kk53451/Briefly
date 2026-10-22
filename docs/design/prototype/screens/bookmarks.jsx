// Bookmarks — saved articles

const BookmarksScreen = () => {
  const items = [
    { title: '한국은행, 기준금리 3.75%로 0.25%p 인상…물가 둔화 더뎌', provider: '연합뉴스', cat: 'economy', savedAt: '오늘 07:15', folder: '경제' },
    { title: '삼성 2나노 양산 개시…"TSMC 추격 9부 능선"', provider: '조선일보', cat: 'tech', savedAt: '오늘 10:02', folder: '읽을거리' },
    { title: '칸 영화제 경쟁부문에 한국영화 3편…역대 최다', provider: '씨네21', cat: 'culture', savedAt: '어제', folder: '읽을거리' },
    { title: '美 CPI 2.4% 둔화…6월 금리인하 확률 72%', provider: '매일경제', cat: 'world', savedAt: '어제', folder: '경제' },
    { title: '전세사기 특별법 5월 1일 시행…2만8천명 구제 길', provider: '한겨레', cat: 'society', savedAt: '4. 16.', folder: '정책' },
    { title: 'GPT-6 등장…"한국어 성능 Gemini 추월"', provider: '전자신문', cat: 'tech', savedAt: '4. 16.', folder: '읽을거리' },
    { title: '현대차 1분기 영업이익 4조 돌파…역대 최대', provider: '조선비즈', cat: 'economy', savedAt: '4. 15.', folder: '경제' },
  ];
  const folders = [
    { id: 'all', label: '전체', count: 28, active: true },
    { id: '경제', label: '경제', count: 11 },
    { id: '읽을거리', label: '읽을거리', count: 9 },
    { id: '정책', label: '정책', count: 5 },
    { id: '기타', label: '기타', count: 3 },
  ];

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>북마크</span>
          <Icon name="search" size={20} color="var(--ink-3)"/>
        </div>
      </div>

      {/* Folders */}
      <div style={{ padding: '10px 24px 10px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {folders.map(f => (
          <span key={f.id} style={{
            padding: '6px 12px', fontFamily: 'var(--sans)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
            border: `1px solid ${f.active ? 'var(--ink)' : 'var(--line)'}`, borderRadius: 999,
            background: f.active ? 'var(--ink)' : 'transparent',
            color: f.active ? 'var(--paper)' : 'var(--ink-2)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}>
            {f.label}
            <span style={{ fontFamily: 'var(--mono)', fontSize: 12, opacity: 0.7 }}>{f.count}</span>
          </span>
        ))}
      </div>

      {/* Sort / action */}
      <div style={{ padding: '12px 24px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-2)', fontWeight: 600 }}>
          <b style={{ color: 'var(--accent)' }}>28</b>개 저장됨
        </span>
        <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>최근 저장순 ▾</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '0 24px 16px' }}>
        {items.map((it, i) => (
          <div key={i} style={{ display: 'flex', gap: 12, padding: '14px 0', borderTop: i === 0 ? '1px solid var(--line)' : '1px solid var(--line-soft)' }}>
            <Placeholder w={72} h={72} label={window.BRIEFLY.CAT_BY_ID[it.cat].ko} cat={it.cat}/>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <CatBadge cat={it.cat}/>
                <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-4)' }}>· {it.folder}</span>
              </div>
              <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, lineHeight: 1.4, marginTop: 4, letterSpacing: '-0.01em', color: 'var(--ink)' }}>
                {it.title}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
                <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)' }}>{it.provider} · {it.savedAt}</span>
                <Icon name="bookmark-filled" size={14} color="var(--accent)"/>
              </div>
            </div>
          </div>
        ))}
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.BookmarksScreen = BookmarksScreen;
