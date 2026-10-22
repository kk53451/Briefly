// News detail + Profile screens

const NewsDetailScreen = ({ variant = 'A' }) => {
  const cat = 'economy';
  const headline = '한국은행, 기준금리 3.75%로 0.25%p 인상…"물가 둔화 더딘 탓"';
  const summary = '한국은행 금융통화위원회가 18일 새벽 본회의를 열고 기준금리를 연 3.5%에서 3.75%로 0.25%포인트 인상하기로 결정했다. 이창용 한은 총재는 "근원물가 둔화가 예상보다 더디고, 주택 가격 상승세가 다시 나타나고 있다"고 배경을 설명했다.';
  const body = `금통위는 이날 오전 긴급 기자회견에서 기준금리 인상 배경을 설명했다. 이창용 총재는 "4월 근원물가가 전년 대비 2.8%로 여전히 목표치인 2%를 웃돌고 있다"고 말했다.

시장 전문가들은 이번 인상이 이미 선반영된 측면이 크다고 평가했다. 원·달러 환율은 발표 직후 1,315원까지 내렸고, 코스피는 장중 0.4% 상승했다.

가계부채 영향도 주목된다. 국민은행은 다음 주부터 주택담보대출 변동금리를 0.2%포인트 인상한다고 밝혔다…`;

  if (variant === 'A') {
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        <div style={{ padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <div style={{ display: 'flex', gap: 18 }}>
            <Icon name="bookmark" size={20} color="var(--ink-3)"/>
            <Icon name="share" size={20} color="var(--ink-3)"/>
            <Icon name="dots" size={20} color="var(--ink-3)"/>
          </div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '10px 24px 24px' }}>
          <CatBadge cat={cat} size="md"/>
          <h1 style={{ fontFamily: 'var(--serif)', fontSize: 26, fontWeight: 900, lineHeight: 1.22, letterSpacing: '-0.02em', marginTop: 10 }}>
            {headline}
          </h1>
          <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 12 }}>
            2026. 4. 18. 금 · 06:10
          </div>
          <div style={{ marginTop: 16 }}>
            <Placeholder h={200} label="한은 총재 기자회견" cat={cat}/>
          </div>
          {/* Summary block */}
          <div style={{ marginTop: 18, display: 'flex', gap: 14 }}>
            <div style={{ width: 3, background: 'var(--accent)', flexShrink: 0 }}/>
            <div>
              <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--accent)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Icon name="sparkle" size={12} color="var(--accent)"/> AI 요약
              </div>
              <p style={{ fontFamily: 'var(--serif)', fontSize: 15, lineHeight: 1.65, color: 'var(--ink)' }}>
                {summary}
              </p>
            </div>
          </div>
          {/* Body */}
          <div style={{ marginTop: 22, fontFamily: 'var(--serif)', fontSize: 16, lineHeight: 1.8, color: 'var(--ink-2)', whiteSpace: 'pre-wrap' }}>
            {body}
          </div>
          <div style={{ marginTop: 22, padding: '12px 14px', background: 'var(--paper-2)', borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', lineHeight: 1.6 }}>
            이 기사는 관련 보도 <b style={{ color: 'var(--ink)' }}>47건</b>의 대표 기사입니다. 다른 시각: 매일경제 · KBS · 한겨레
          </div>
        </div>
        <div style={{ padding: '12px 24px 12px', borderTop: '1px solid var(--line)', background: 'var(--card)' }}>
          <button style={{ width: '100%', padding: '14px', background: 'var(--ink)', color: 'var(--paper)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 14, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            원문 보기
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M7 17L17 7M9 7h8v8"/></svg>
          </button>
        </div>
        <HomeIndicator/>
      </div>
    );
  }

  // B — long-read immersive with drop cap
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ height: 260, background: window.BRIEFLY.CAT_BY_ID[cat].color, position: 'relative', padding: '14px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Icon name="arrow-left" size={22} color="var(--paper)"/>
            <Icon name="bookmark" size={20} color="var(--paper)"/>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'rgba(247,242,233,0.9)' }}>경제 · 금융통화위원회</div>
            <h1 style={{ fontFamily: 'var(--serif)', fontSize: 28, fontWeight: 900, lineHeight: 1.15, color: 'var(--paper)', marginTop: 8, letterSpacing: '-0.02em' }}>
              {headline}
            </h1>
          </div>
        </div>
        <div style={{ padding: '18px 24px 24px' }}>
          <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', display: 'flex', justifyContent: 'space-between' }}>
            <span>연합뉴스 · 김민수 기자</span><span>4. 18. · 06:10</span>
          </div>
          <div style={{ marginTop: 18, fontFamily: 'var(--serif)', fontSize: 16, lineHeight: 1.8, color: 'var(--ink)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 60, float: 'left', lineHeight: 0.9, marginRight: 8, marginTop: 6, color: 'var(--accent)' }}>한</span>
            국은행 금융통화위원회가 18일 새벽 본회의를 열고 기준금리를 연 3.5%에서 3.75%로 0.25%포인트 인상하기로 결정했다. 이창용 한은 총재는 "근원물가 둔화가 예상보다 더디고, 주택 가격 상승세가 다시 나타나고 있다"고 배경을 설명했다.
          </div>
          <p style={{ fontFamily: 'var(--serif)', fontSize: 16, lineHeight: 1.8, color: 'var(--ink-2)', marginTop: 16 }}>
            시장 전문가들은 이번 인상이 이미 선반영된 측면이 크다고 평가했다. 원·달러 환율은 발표 직후 1,315원까지 내렸고, 코스피는 장중 0.4% 상승했다.
          </p>
          <div style={{ margin: '22px -6px', padding: '18px 20px', background: 'var(--paper-2)', borderLeft: `4px solid var(--accent)` }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 600, lineHeight: 1.45, color: 'var(--ink)' }}>
              "근원물가가 2%대로 안착할 때까지 긴축 기조를 유지할 것"
            </div>
            <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 8 }}>— 이창용 한은 총재</div>
          </div>
        </div>
      </div>
      <HomeIndicator/>
    </div>
  );
};

const ProfileScreen = ({ variant = 'A' }) => {
  const selected = ['economy', 'politics', 'world', 'tech'];

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 10px', borderBottom: '2px solid var(--ink)' }}>
        <BrieflyMark size={18}/>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Profile card */}
        <div style={{ padding: '24px 24px 18px', display: 'flex', gap: 16, alignItems: 'center', borderBottom: '1px solid var(--line)' }}>
          <div style={{ width: 64, height: 64, borderRadius: 999, background: 'var(--accent-soft)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 26, color: 'var(--accent)' }}>독</span>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 20, fontWeight: 700 }}>독자 #A7B9</div>
            <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4 }}>게스트 구독 · 3월 12일 시작</div>
          </div>
        </div>
        {/* Stats — newspaper-style */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--line)' }}>
          {[['38', '함께한 일'], ['108', '들은 에피소드']].map(([v, l], i, arr) => (
            <div key={i} style={{ flex: 1, padding: '16px 12px', textAlign: 'center', borderRight: i < arr.length - 1 ? '1px solid var(--line-soft)' : 'none' }}>
              <div style={{ fontFamily: 'var(--serif)', fontSize: 28, fontWeight: 900, color: 'var(--ink)', letterSpacing: '-0.02em' }}>{v}</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.04em', marginTop: 4 }}>{l}</div>
            </div>
          ))}
        </div>
        {/* Settings list */}
        <div style={{ padding: '6px 24px 0' }}>
          <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.14em', marginBottom: 4, paddingTop: 16, borderTop: '1px solid var(--line)' }}>설정</div>
          {[
            { icon: 'sparkle', label: '관심 주제 편집', detail: `${selected.length}개 선택됨 · ${selected.map(id => window.BRIEFLY.CAT_BY_ID[id].ko).join(', ')}`, chevron: true },
            { icon: 'type', label: '폰트 설정', detail: '제목 · Noto Serif KR · 본문 · Pretendard', chevron: true },
            { icon: 'sun', label: '다크 모드', toggle: 'theme' },
            { icon: 'bookmark', label: '북마크', detail: '28개 저장됨', chevron: true },
            { icon: 'bell', label: '알림', detail: 'AM 07:30 · PM 18:00', chevron: true },
            { icon: 'info', label: '앱 정보', chevron: true },
          ].map((r, i, arr) => (
            <window.ThemeCtx.Consumer key={i}>
              {(themeCtx) => {
                const isDark = themeCtx && themeCtx.theme === 'dark';
                return (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 0', borderBottom: i < arr.length - 1 ? '1px solid var(--line-soft)' : 'none' }}>
                    <div style={{ width: 32, height: 32, borderRadius: 4, background: 'var(--paper-2)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Icon name={r.toggle === 'theme' && isDark ? 'moon' : r.icon} size={16} color="var(--ink-2)"/>
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 600 }}>{r.label}</div>
                      {r.detail && <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.detail}</div>}
                    </div>
                    {r.toggle === 'theme' ? (
                      <div
                        onClick={() => themeCtx && themeCtx.setTheme(isDark ? 'light' : 'dark')}
                        style={{
                          width: 40, height: 22, borderRadius: 999,
                          background: isDark ? 'var(--accent)' : 'var(--line)',
                          position: 'relative', padding: 2, cursor: 'pointer',
                          transition: 'background 200ms ease',
                        }}>
                        <div style={{
                          width: 18, height: 18, borderRadius: 999,
                          background: 'var(--paper)',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
                          transform: isDark ? 'translateX(18px)' : 'translateX(0)',
                          transition: 'transform 200ms ease',
                        }}/>
                      </div>
                    ) : <Icon name="chevron-right" size={16} color="var(--ink-4)"/>}
                  </div>
                );
              }}
            </window.ThemeCtx.Consumer>
          ))}
        </div>
        <div style={{ padding: '20px 24px' }}>
          <button style={{ width: '100%', padding: '14px', background: 'transparent', color: 'var(--ink)', border: 0, fontFamily: 'var(--sans)', fontSize: 13.5, fontWeight: 600, cursor: 'pointer' }}>
            로그아웃
          </button>
        </div>
      </div>
      <TabBar active="profile"/>
      <HomeIndicator/>
    </div>
  );
};

window.NewsDetailScreen = NewsDetailScreen;
window.ProfileScreen = ProfileScreen;
