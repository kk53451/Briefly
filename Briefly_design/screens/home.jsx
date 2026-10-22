// Home screen — category-filtered news list

const HomeScreen = ({ variant = 'A', category = 'economy' }) => {
  const cats = window.BRIEFLY.CATEGORIES;
  const news = window.BRIEFLY.NEWS_BY_CATEGORY[category] || window.BRIEFLY.NEWS_BY_CATEGORY.economy;
  const activeCat = window.BRIEFLY.CAT_BY_ID[category];
  const tabs = [{ id: 'all', ko: '종합' }, { id: 'my', ko: 'MY' }, ...cats];

  const Masthead = (
    <div style={{ padding: '14px 24px 10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '2px solid var(--ink)', paddingBottom: 10 }}>
        <div>
          <BrieflyMark size={18}/>
        </div>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center', color: 'var(--ink-3)' }}>
          <Icon name="search" size={18}/>
          <Icon name="bell" size={18}/>
        </div>
      </div>
    </div>
  );

  const CatTabs = (
    <div style={{ borderBottom: '1px solid var(--line)' }}>
      <div style={{ display: 'flex', gap: 2, padding: '10px 16px', overflow: 'auto' }}>
        {tabs.map(t => {
          const on = t.id === category || (category === 'all' && t.id === 'all');
          const c = window.BRIEFLY.CAT_BY_ID[t.id];
          return (
            <div key={t.id} style={{
              minHeight: 44, padding: '10px 14px', fontFamily: 'var(--serif)', fontWeight: on ? 700 : 500,
              fontSize: 16, letterSpacing: '-0.01em', whiteSpace: 'nowrap',
              display: 'inline-flex', alignItems: 'center',
              color: on ? 'var(--ink)' : 'var(--ink-3)',
              borderBottom: on ? `2px solid ${c ? c.color : 'var(--ink)'}` : '2px solid transparent',
              marginBottom: -1, flexShrink: 0,
            }}>
              {t.ko}
            </div>
          );
        })}
      </div>
    </div>
  );

  const SortBar = (
    <div style={{ padding: '12px 24px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontFamily: 'var(--sans)', fontSize: 14, color: 'var(--ink-2)', fontWeight: 600, minHeight: 36, padding: '4px 0' }}>
        <Icon name="sort" size={16}/> 트렌드순 <Icon name="chevron-down" size={16}/>
      </div>
      <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>2026. 4. 18. 07:22 업데이트</span>
    </div>
  );

  if (variant === 'A') {
    // Horizontal card: rank number, headline, thumb
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        {Masthead}
        {CatTabs}
        {SortBar}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 24px 16px' }}>
          {/* Lead story */}
          <div style={{ paddingBottom: 18, borderBottom: '1px solid var(--line)' }}>
            <Placeholder h={180} label="리드 사진" cat={category}/>
            <div style={{ marginTop: 12 }}>
              <CatBadge cat={category}/>
              <h2 style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 800, lineHeight: 1.25, marginTop: 8, letterSpacing: '-0.02em' }}>
                {news[0].title}
              </h2>
              <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)', marginTop: 8, display: 'flex', gap: 8 }}>
                <span>{news[0].provider}</span><span>·</span>
                <span>관련 {news[0].cluster_size}건</span><span>·</span>
                <span>{news[0].published_at}</span>
              </div>
            </div>
          </div>

          {news.slice(1).map((n, i) => (
            <div key={i} style={{ display: 'flex', gap: 14, padding: '16px 0', borderBottom: i < news.length - 2 ? '1px solid var(--line-soft)' : 'none' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>#{n.rank}</span>
                  <CatBadge cat={category}/>
                </div>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700, lineHeight: 1.4, color: 'var(--ink)', letterSpacing: '-0.01em' }}>{n.title}</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)', marginTop: 8 }}>
                  {n.provider} · 관련 {n.cluster_size}건 · {n.published_at}
                </div>
              </div>
              <Placeholder w={84} h={84} label={String(n.rank)} cat={category}/>
            </div>
          ))}
        </div>
        <TabBar active="home"/>
        <HomeIndicator/>
      </div>
    );
  }

  if (variant === 'B') {
    // Newspaper column — no thumbs, serif dense index
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        {Masthead}
        {CatTabs}
        {SortBar}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 24px 16px' }}>
          {news.map((n, i) => (
            <div key={i} style={{
              padding: '16px 0',
              borderTop: i === 0 ? '2px solid var(--ink)' : '1px solid var(--line-soft)',
              display: 'flex', gap: 14, alignItems: 'flex-start',
            }}>
              <div style={{
                fontFamily: 'var(--serif)', fontSize: 38, fontWeight: 900,
                color: 'var(--ink-4)', lineHeight: 0.85, width: 42, flexShrink: 0,
              }}>{String(n.rank).padStart(2, '0')}</div>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 700, lineHeight: 1.3, letterSpacing: '-0.015em', color: 'var(--ink)' }}>
                  {n.title}
                </h3>
                <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 8 }}>
                  {n.provider} · 관련 기사 {n.cluster_size}건 · {n.published_at}
                </div>
              </div>
              {n.rank <= 3 && (
                <span style={{
                  fontFamily: 'var(--mono)', fontSize: 12, padding: '3px 8px', borderRadius: 2,
                  background: 'var(--accent)', color: 'var(--paper)', letterSpacing: '0.04em', fontWeight: 700,
                  alignSelf: 'flex-start',
                }}>주목</span>
              )}
            </div>
          ))}
        </div>
        <TabBar active="home"/>
        <HomeIndicator/>
      </div>
    );
  }

  // C — card deck with large photos
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper-2)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      {Masthead}
      {CatTabs}
      {SortBar}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 16px 16px' }}>
        {news.map((n, i) => (
          <div key={i} style={{
            background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 4,
            marginBottom: 10, overflow: 'hidden', display: 'flex', gap: 0,
          }}>
            <Placeholder w={110} h={110} label={activeCat.ko} cat={category} radius={0}/>
            <div style={{ flex: 1, padding: 12, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <CatBadge cat={category}/>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)' }}>#{n.rank}</span>
                </div>
                <div style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, lineHeight: 1.4, marginTop: 8, color: 'var(--ink)' }}>
                  {n.title.length > 60 ? n.title.slice(0, 58) + '…' : n.title}
                </div>
              </div>
              <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 8 }}>
                {n.provider} · {n.cluster_size}건 · {n.published_at}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ background: 'var(--card)' }}>
        <TabBar active="home"/>
        <HomeIndicator/>
      </div>
    </div>
  );
};

window.HomeScreen = HomeScreen;
