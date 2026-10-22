// Category index — overview of all categories

const CategoryIndexScreen = () => {
  const cats = window.BRIEFLY.CATEGORIES;

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em' }}>카테고리</span>
          <Icon name="search" size={20} color="var(--ink-3)"/>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Subscribed */}
        <div style={{ padding: '18px 24px 8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, color: 'var(--ink-2)' }}>구독 중</span>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 14, color: 'var(--accent)', fontWeight: 600, minHeight: 32, padding: '6px 4px', display: 'inline-flex', alignItems: 'center' }}>편집</span>
          </div>
        </div>
        <div style={{ padding: '0 16px 6px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {cats.filter((c, i) => i < 4).map(c => {
              const count = (window.BRIEFLY.NEWS_BY_CATEGORY[c.id] || []).length;
              return (
                <div key={c.id} style={{
                  borderRadius: 2, background: 'var(--card)',
                  border: '1px solid var(--line)', borderLeft: `3px solid ${c.color}`,
                  padding: '14px 14px', display: 'flex', flexDirection: 'column', gap: 8,
                  position: 'relative',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Icon name={c.icon} size={22} color={c.color} strokeWidth={1.5}/>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.06em' }}>{count}건</span>
                  </div>
                  <div>
                    <div style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 800, color: 'var(--ink)', letterSpacing: '-0.01em' }}>{c.ko}</div>
                    <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4 }}>오늘 · 업데이트됨</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* All */}
        <div style={{ padding: '24px 24px 8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, color: 'var(--ink-2)' }}>전체 주제</span>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>{cats.length}개</span>
          </div>
        </div>
        <div style={{ padding: '0 24px 16px' }}>
          {cats.map((c, i) => {
            const subscribed = i < 4;
            const count = (window.BRIEFLY.NEWS_BY_CATEGORY[c.id] || []).length;
            return (
              <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 0', minHeight: 56, borderBottom: i < cats.length - 1 ? '1px solid var(--line-soft)' : 'none' }}>
                <div style={{ width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${c.color}15`, borderRadius: 2 }}>
                  <Icon name={c.icon} size={20} color={c.color} strokeWidth={1.6}/>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 700, letterSpacing: '-0.01em' }}>{c.ko}</div>
                  <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4 }}>오늘 {count}건 · 이번 주 {count * 7}건</div>
                </div>
                {subscribed ? (
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--paper)', background: 'var(--ink)', padding: '6px 12px', letterSpacing: '0.08em', minHeight: 32, display: 'inline-flex', alignItems: 'center' }}>구독</span>
                ) : (
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-2)', border: '1px solid var(--ink-2)', padding: '6px 12px', letterSpacing: '0.08em', minHeight: 32, display: 'inline-flex', alignItems: 'center' }}>+ 구독</span>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.CategoryIndexScreen = CategoryIndexScreen;
