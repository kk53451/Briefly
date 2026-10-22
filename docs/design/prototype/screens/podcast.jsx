// Podcast screen — "오늘의 팟캐스트" (AM/PM 브리핑, not per-category)
// Variants: A = minimal paper player, B = detail w/ script + today's episodes

const PodcastScreen = ({ variant = 'A', slot = 'AM' }) => {
  const episodes = window.BRIEFLY.PODCAST_EPISODES;
  const todayEps = episodes.filter(e => e.date === '4. 18.');
  const current = todayEps.find(e => e.slot === slot) || todayEps[1];
  const script = window.BRIEFLY.SCRIPTS[current.scriptKey] || window.BRIEFLY.SCRIPTS.am;
  const relatedNews = (slot === 'AM' ? window.BRIEFLY.BRIEFING_AM : window.BRIEFLY.BRIEFING_PM);
  const progress = 0.38;
  const accent = 'var(--accent)';

  const Controls = ({ dark = false }) => {
    const c = dark ? 'var(--paper)' : 'var(--ink)';
    const sideBtn = {
      background: 'none', border: `1px solid ${dark ? 'rgba(247,242,233,0.25)' : 'var(--line)'}`,
      borderRadius: 999, padding: '6px 12px',
      color: dark ? 'rgba(247,242,233,0.7)' : 'var(--ink-3)', cursor: 'pointer',
      fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 700, letterSpacing: '0.08em',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 48, height: 32,
    };
    const iconBtn = {
      background: 'none', border: 0, color: c, cursor: 'pointer',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      width: 44, height: 44,
    };
    return (
      <div style={{ marginTop: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 64px 1fr 1fr', alignItems: 'center', justifyItems: 'center', gap: 0 }}>
          <button style={sideBtn}>1.0×</button>
          <button style={iconBtn}>
            <Icon name="track-prev" size={26} color={c}/>
          </button>
          <button style={{
            width: 64, height: 64, borderRadius: 999, background: c, color: dark ? accent : 'var(--paper)',
            border: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
          }}>
            <Icon name="play" size={26} color={dark ? accent : 'var(--paper)'}/>
          </button>
          <button style={iconBtn}>
            <Icon name="track-next" size={26} color={c}/>
          </button>
          <button style={sideBtn}>
            <Icon name="list" size={14} color={dark ? 'rgba(247,242,233,0.7)' : 'var(--ink-3)'}/>
          </button>
        </div>
      </div>
    );
  };

  const Progress = ({ dark = false }) => (
    <div>
      <div style={{ height: 3, background: dark ? 'rgba(247,242,233,0.25)' : 'var(--line)', borderRadius: 2, position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${progress*100}%`, background: dark ? 'var(--paper)' : 'var(--ink)', borderRadius: 2 }}/>
        <div style={{ position: 'absolute', left: `${progress*100}%`, top: '50%', width: 12, height: 12, borderRadius: 999, background: dark ? 'var(--paper)' : 'var(--ink)', transform: 'translate(-50%, -50%)' }}/>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontFamily: 'var(--mono)', fontSize: 12, color: dark ? 'rgba(247,242,233,0.7)' : 'var(--ink-3)', letterSpacing: '0.06em' }}>
        <span>01:53</span><span>{current.duration}</span>
      </div>
    </div>
  );

  if (variant === 'A') {
    // A — "지금 듣고 있는 아티클" 리스트 + 하단 고정 플레이어
    // 현재 재생 중인 브리핑이 다루는 기사들을 시간 순으로 보여주고, 하단에 미니 풀-플레이어를 둔다.
    const articles = relatedNews.slice(0, 5);

    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        {/* Header */}
        <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="chevron-down" size={22} color="var(--ink-3)"/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>지금 듣는 중</span>
          <Icon name="dots" size={22} color="var(--ink-3)"/>
        </div>

        {/* Section title */}
        <div style={{ padding: '20px 24px 10px' }}>
          <div style={{ fontFamily: 'var(--label)', fontSize: 11, color: accent, letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 6 }}>Now Playing · {current.slotKo}</div>
          <h2 style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 900, letterSpacing: '-0.025em', lineHeight: 1.2, color: 'var(--ink)' }}>
            지금 듣고 있는 아티클
          </h2>
          <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4 }}>
            이 브리핑이 다루는 기사 {articles.length}건
          </div>
        </div>

        {/* Article list */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 24px 200px' }}>
          {articles.map((t, i) => {
            const cat = window.BRIEFLY.CAT_BY_ID[t.category];
            const isActive = i === 1; // mock: 두 번째 기사 재생 중
            return (
              <div key={t.topic_id} style={{
                display: 'flex', gap: 14, padding: '16px 0',
                borderBottom: i < articles.length - 1 ? '1px solid var(--line-soft)' : 'none',
                position: 'relative',
                alignItems: 'center',
              }}>
                {isActive && <div style={{ position: 'absolute', left: -12, top: '50%', marginTop: -12, width: 3, height: 24, background: accent, borderRadius: 2 }}/>}
                {/* Thumbnail (left) */}
                <div style={{
                  flexShrink: 0, width: 64, height: 64, borderRadius: 4, overflow: 'hidden',
                  position: 'relative',
                  border: '1px solid var(--line)',
                  background: 'var(--paper-2)',
                  filter: isActive ? 'none' : 'grayscale(0.25)',
                }}>
                  {/* placeholder image: diagonal stripes + tone */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    background: `linear-gradient(135deg, var(--cat-${t.category}) 0%, var(--ink) 160%)`,
                  }}/>
                  <div style={{
                    position: 'absolute', inset: 0,
                    backgroundImage: 'repeating-linear-gradient(135deg, rgba(247,242,233,0.08) 0 4px, transparent 4px 9px)',
                  }}/>
                  <div style={{
                    position: 'absolute', inset: 0,
                    border: '1px solid rgba(247,242,233,0.18)',
                    margin: 5,
                  }}/>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <span className="cat-dot" style={{ background: `var(--cat-${t.category})` }}/>
                    <span style={{ fontFamily: 'var(--label)', fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>{cat.ko}</span>
                  </div>
                  <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 800, letterSpacing: '-0.018em', lineHeight: 1.32, color: 'var(--ink)' }}>
                    {t.headline}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Fixed bottom full-player */}
        <div style={{
          position: 'absolute', left: 0, right: 0, bottom: 49 + 24, // tab bar (49) + home indicator
          background: 'var(--paper)', borderTop: '1px solid var(--line)',
          padding: '14px 24px 14px',
          boxShadow: '0 -10px 28px rgba(26,23,20,0.06)',
        }}>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 900, letterSpacing: '-0.022em', color: 'var(--ink)', lineHeight: 1.2 }}>
            {current.dateKo} · {current.slotKo} 브리핑
          </div>
          <div style={{ marginTop: 10 }}>
            <Progress/>
          </div>
          <div style={{ marginTop: 6 }}>
            <Controls/>
          </div>
        </div>

        <TabBar active="podcast"/>
        <HomeIndicator/>

        <style>{`
          @keyframes briefly-pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.7); }
          }
        `}</style>
      </div>
    );
  }

  // B — detail with script + today's AM/PM + recent episodes
  const recent = episodes.slice(0, 6);
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>팟캐스트</span>
          <Icon name="share" size={20} color="var(--ink-4)"/>
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* Wide album art */}
        <div style={{ height: 180, background: 'var(--ink)', position: 'relative', padding: '20px 24px', color: 'var(--paper)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.12em', color: accent }}>● VOL. 108 · {current.slot}</span>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, opacity: 0.9 }}>2026. 4. 18. · {current.slotKo}</span>
          </div>
          <div>
            <div style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 36, letterSpacing: '-0.03em', lineHeight: 1 }}>오늘의 팟캐스트</div>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 14, opacity: 0.85, marginTop: 6 }}>{current.dateKo} · {current.slotKo} 브리핑 · {current.duration}</div>
          </div>
        </div>
        <div style={{ padding: '18px 24px 10px' }}>
          <h2 style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.35, marginBottom: 14 }}>
            {current.subtitle}
          </h2>
          <Progress/>
          <Controls/>
        </div>
        {/* Related news — 이 브리핑에서 다룬 뉴스 */}
        <div style={{ padding: '18px 24px 12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12, paddingBottom: 8, borderBottom: '1px solid var(--line)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 13, fontWeight: 700, letterSpacing: '-0.01em', color: accent }}>이 브리핑의 뉴스</span>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)' }}>{relatedNews.length}개</span>
          </div>
          {relatedNews.map((t, i) => {
            const cat = window.BRIEFLY.CAT_BY_ID[t.category];
            return (
              <div key={t.topic_id} style={{ display: 'flex', gap: 12, padding: '12px 0', borderBottom: i < relatedNews.length - 1 ? '1px solid var(--line-soft)' : 'none', cursor: 'pointer' }}>
                <div style={{ flexShrink: 0, width: 28, textAlign: 'center' }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-4)', letterSpacing: '0.08em' }}>{String(i + 1).padStart(2, '0')}</div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <span className="cat-dot" style={{ background: `var(--cat-${t.category})` }}/>
                    <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.08em' }}>{cat.ko}</span>
                    <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-4)' }}>· 관련 보도 {t.cluster_size}건</span>
                  </div>
                  <div style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, letterSpacing: '-0.015em', lineHeight: 1.35, color: 'var(--ink)' }}>
                    {t.headline}
                  </div>
                  <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 4, lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {t.summary}
                  </div>
                </div>
                <Icon name="chevron-right" size={14} color="var(--ink-4)"/>
              </div>
            );
          })}
        </div>
        {/* Recent episodes — today + past */}
        <div style={{ padding: '8px 24px 24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingBottom: 10, borderBottom: '1px solid var(--line)' }}>
            <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.1em' }}>최근 에피소드</span>
            <span style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)' }}>전체 ›</span>
          </div>
          {recent.map((e, i) => {
            const isCur = e.id === current.id;
            const isUp = e.status === 'upcoming';
            return (
              <div key={e.id} style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 0', borderBottom: i < recent.length - 1 ? '1px solid var(--line-soft)' : 'none', opacity: isUp ? 0.55 : 1 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 2,
                  background: isCur ? accent : (isUp ? 'var(--paper-2)' : 'var(--ink)'),
                  border: isUp ? `1px dashed var(--ink-4)` : 'none',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                }}>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.1em', color: isUp ? 'var(--ink-3)' : 'var(--paper)', opacity: 0.75 }}>{e.date}</div>
                  <div style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 13, color: isUp ? 'var(--ink-3)' : 'var(--paper)', marginTop: 1 }}>{e.slot}</div>
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                    <span style={{ fontFamily: 'var(--serif)', fontSize: 14, fontWeight: 700, color: isCur ? accent : 'var(--ink)' }}>
                      {e.dateKo} {e.slotKo}
                    </span>
                    {isCur && <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: accent }}>●</span>}
                    {isUp && <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.08em', color: 'var(--ink-3)' }}>예정</span>}
                  </div>
                  <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {e.subtitle}
                  </div>
                  <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-4)', marginTop: 3 }}>
                    {isUp ? '18:00 발행 예정' : e.duration}
                  </div>
                </div>
                {isCur ? <Icon name="volume" size={18} color={accent}/> : (isUp ? <Icon name="bell" size={16} color="var(--ink-4)"/> : <Icon name="play" size={16} color="var(--ink-3)"/>)}
              </div>
            );
          })}
        </div>
      </div>
      <TabBar active="podcast"/>
      <HomeIndicator/>
    </div>
  );
};

window.PodcastScreen = PodcastScreen;
