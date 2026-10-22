// Notifications — editorial feed of alerts

const NotificationsScreen = () => {
  const groups = [
    {
      label: '오늘', items: [
        { type: 'briefing', icon: 'newspaper', title: '오전 브리핑이 준비됐어요', sub: '금리 3.75% 인상, 추경 35조 합의 외 4건', time: '07:30', unread: true },
        { type: 'breaking', icon: 'alert', title: '속보 · 한국은행 기준금리 인상', sub: '3.5% → 3.75%, 0.25%p 인상 결정', time: '06:12', unread: true, accent: true },
        { type: 'topic', icon: 'bookmark', title: '관심 토픽 업데이트', sub: '‘삼성 2나노’ 관련 기사 3건이 추가됐어요', time: '10:30', unread: true },
      ]
    },
    {
      label: '어제', items: [
        { type: 'briefing', icon: 'radio', title: '오후 브리핑 · 4월 17일', sub: '반도체 수출 2년 만 최대 외 4건', time: '18:00' },
        { type: 'topic', icon: 'trending', title: '경제 지표 요약 — 주간', sub: '코스피, 환율, 금리 한눈에 보기', time: '09:00' },
        { type: 'digest', icon: 'sparkle', title: '이번 주 많이 읽은 기사 5선', sub: '박찬욱 신작, LG엔솔 전고체, …', time: '08:00' },
      ]
    },
    {
      label: '이번 주', items: [
        { type: 'system', icon: 'info', title: '관심 카테고리를 업데이트하셨어요', sub: '경제, 정치, 국제, IT/과학 — 총 4개', time: '4. 16. 21:14' },
        { type: 'digest', icon: 'bell', title: '알림 시간 변경 안내', sub: '오전 07:30 · 오후 18:00로 설정됨', time: '4. 15. 10:00' },
      ]
    },
  ];

  const Row = ({ n }) => (
    <div style={{ display: 'flex', gap: 14, padding: '14px 0', borderBottom: '1px solid var(--line-soft)', position: 'relative' }}>
      {n.unread && <div style={{ position: 'absolute', left: -10, top: 22, width: 5, height: 5, borderRadius: 999, background: n.accent ? 'var(--accent)' : 'var(--ink)' }}/>}
      <div style={{
        width: 38, height: 38, borderRadius: 4, flexShrink: 0,
        background: n.accent ? 'var(--accent)' : 'var(--paper-2)',
        border: n.accent ? 'none' : '1px solid var(--line)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon name={n.icon} size={18} color={n.accent ? 'var(--paper)' : 'var(--ink-2)'} strokeWidth={1.6}/>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, color: 'var(--ink)', letterSpacing: '-0.01em' }}>
            {n.accent && <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.1em', marginRight: 6 }}>● LIVE</span>}
            {n.title}
          </div>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', flexShrink: 0, letterSpacing: '0.04em' }}>{n.time}</span>
        </div>
        <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-2)', marginTop: 4, lineHeight: 1.5 }}>
          {n.sub}
        </div>
      </div>
    </div>
  );

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>알림</span>
          <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)' }}>모두 읽음</span>
        </div>
      </div>

      {/* Filter */}
      <div style={{ padding: '10px 24px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {[
          { id: 'all', label: '전체', count: 8, active: true },
          { id: 'unread', label: '안 읽음', count: 3 },
          { id: 'briefing', label: '브리핑' },
          { id: 'breaking', label: '속보' },
        ].map(c => (
          <span key={c.id} style={{
            padding: '5px 11px', fontFamily: 'var(--sans)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
            border: `1px solid ${c.active ? 'var(--ink)' : 'var(--line)'}`, borderRadius: 999,
            background: c.active ? 'var(--ink)' : 'transparent',
            color: c.active ? 'var(--paper)' : 'var(--ink-2)',
          }}>{c.label}{c.count ? ` ${c.count}` : ''}</span>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '0 24px' }}>
        {groups.map((g, i) => (
          <div key={i}>
            <div style={{ padding: '18px 0 6px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <span style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, color: 'var(--ink-2)', letterSpacing: '-0.01em' }}>{g.label}</span>
              <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>{g.items.length}건</span>
            </div>
            {g.items.map((n, j) => <Row key={j} n={n}/>)}
          </div>
        ))}
        <div style={{ padding: '24px 0', textAlign: 'center', fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-4)' }}>
          30일 이전 알림은 자동 삭제됩니다
        </div>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.NotificationsScreen = NotificationsScreen;
