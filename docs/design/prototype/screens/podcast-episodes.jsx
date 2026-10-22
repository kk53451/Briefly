// Podcast episodes list — newspaper-style catalog of "오늘의 팟캐스트" (AM/PM, not per-category)

const PodcastEpisodesScreen = () => {
  const episodes = window.BRIEFLY.PODCAST_EPISODES;

  // Group by date
  const byDate = {};
  episodes.forEach(e => {
    if (!byDate[e.date]) byDate[e.date] = { date: e.date, dateKo: e.dateKo, day: e.day, eps: [] };
    byDate[e.date].eps.push(e);
  });
  const groups = Object.values(byDate);
  // Label today / yesterday
  groups[0] && (groups[0].label = '오늘');
  groups[1] && (groups[1].label = '어제');

  const Row = ({ ep }) => {
    const isPlaying = ep.status === 'playing';
    const isUpcoming = ep.status === 'upcoming';
    return (
      <div style={{
        display: 'flex', gap: 12, alignItems: 'center', padding: '12px 0',
        borderBottom: '1px solid var(--line-soft)',
        opacity: isUpcoming ? 0.5 : 1,
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 2,
          background: isPlaying ? 'var(--accent)' : (isUpcoming ? 'var(--paper-2)' : 'var(--ink)'),
          border: isUpcoming ? `1px dashed var(--ink-4)` : 'none',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.1em', color: isUpcoming ? 'var(--ink-3)' : 'rgba(247,242,233,0.8)' }}>{ep.date}</div>
          <div style={{ fontFamily: 'var(--serif)', fontWeight: 900, fontSize: 14, color: isUpcoming ? 'var(--ink-3)' : 'var(--paper)', lineHeight: 1, marginTop: 2 }}>
            {ep.slot}
          </div>
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 15, fontWeight: 700, color: isPlaying ? 'var(--accent)' : 'var(--ink)' }}>
              {ep.slotKo} 브리핑
            </span>
            {isPlaying && <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--accent)' }}>●</span>}
            {isUpcoming && <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.08em', color: 'var(--ink-3)' }}>예정</span>}
          </div>
          <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {ep.subtitle}
          </div>
          <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-4)', marginTop: 3 }}>
            {isUpcoming ? '18:00 발행 예정' : `${ep.duration} · ${ep.listens.toLocaleString()}회 청취`}
          </div>
        </div>
        {isUpcoming ? (
          <Icon name="bell" size={16} color="var(--ink-4)"/>
        ) : isPlaying ? (
          <Icon name="volume" size={18} color="var(--accent)"/>
        ) : (
          <Icon name="play" size={16} color="var(--ink-3)"/>
        )}
      </div>
    );
  };

  const SectionHead = ({ g }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '18px 24px 6px' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontFamily: 'var(--serif)', fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em' }}>
          {g.label || `${g.dateKo} (${g.day})`}
        </span>
        {g.label && <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>{g.dateKo} {g.day}</span>}
      </div>
      <span style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)' }}>{g.eps.length}편</span>
    </div>
  );

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      {/* Header — newspaper masthead */}
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="chevron-left" size={22} color="var(--ink)"/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>팟캐스트 목록</span>
          <Icon name="search" size={20} color="var(--ink-3)"/>
        </div>
      </div>

      {/* Filter chips — AM/PM toggle */}
      <div style={{ padding: '10px 24px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {[
          { id: 'all', label: '전체', active: true },
          { id: 'am', label: '오전 AM' },
          { id: 'pm', label: '오후 PM' },
          { id: 'saved', label: '저장됨' },
        ].map(chip => (
          <span key={chip.id} style={{
            padding: '5px 11px', fontFamily: 'var(--sans)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap',
            border: `1px solid ${chip.active ? 'var(--ink)' : 'var(--line)'}`, borderRadius: 999,
            background: chip.active ? 'var(--ink)' : 'transparent',
            color: chip.active ? 'var(--paper)' : 'var(--ink-2)',
          }}>{chip.label}</span>
        ))}
      </div>

      {/* List */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {groups.map((g, i) => (
          <div key={i}>
            <SectionHead g={g}/>
            <div style={{ padding: '2px 24px 0' }}>
              {g.eps.map(ep => <Row key={ep.id} ep={ep}/>)}
            </div>
          </div>
        ))}

        <div style={{ padding: '20px 24px 30px', textAlign: 'center' }}>
          <button style={{
            padding: '10px 20px', background: 'transparent', border: '1px solid var(--line)', borderRadius: 2,
            fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', cursor: 'pointer',
          }}>
            더 불러오기
          </button>
        </div>
      </div>
      <TabBar active="podcast"/>
      <HomeIndicator/>
    </div>
  );
};

window.PodcastEpisodesScreen = PodcastEpisodesScreen;
