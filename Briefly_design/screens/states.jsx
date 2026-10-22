// Empty / Loading / Error states — editorial tone

// ─── Loading ─── Skeleton with shimmer sweep
const LoadingState = () => {
  // Shimmer bar — animated diagonal gradient sweep.
  // Uses CSS keyframe in inline <style> tag shared across bars.
  const bar = (w, h = 10) => (
    <div style={{
      width: w, height: h, borderRadius: 2, overflow: 'hidden',
      background: 'var(--paper-2)', position: 'relative',
    }}>
      <div className="briefly-shimmer"/>
    </div>
  );
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <style>{`
        @keyframes brieflyShimmer {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
        @keyframes brieflyDotPulse {
          0%, 100% { opacity: 0.2; }
          50%      { opacity: 1;   }
        }
        .briefly-shimmer {
          position: absolute; inset: 0;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(160,58,40,0.08) 40%,
            rgba(160,58,40,0.22) 50%,
            rgba(160,58,40,0.08) 60%,
            transparent 100%
          );
          animation: brieflyShimmer 1.6s ease-in-out infinite;
        }
        .briefly-shimmer-thumb {
          position: relative; overflow: hidden;
        }
        .briefly-shimmer-thumb::after {
          content: ''; position: absolute; inset: 0;
          background: linear-gradient(
            110deg,
            transparent 20%,
            rgba(247,242,233,0.5) 50%,
            transparent 80%
          );
          animation: brieflyShimmer 1.8s ease-in-out infinite;
        }
        .briefly-dot { animation: brieflyDotPulse 1.4s ease-in-out infinite; }
      `}</style>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '2px solid var(--ink)', paddingBottom: 10 }}>
          <BrieflyMark size={18}/>
          <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.08em' }}>
            <span className="briefly-dot">●</span> 가져오는 중
          </span>
        </div>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: 32, fontWeight: 900, letterSpacing: '-0.03em', marginTop: 14 }}>
          오늘의 브리핑
        </h1>
      </div>
      <div style={{ padding: '8px 24px 14px' }}>
        <div style={{ display: 'flex', gap: 4 }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} style={{
              flex: 1, height: 3, borderRadius: 2,
              background: i === 0 ? 'var(--ink)' : 'var(--line)',
              opacity: i === 0 ? 1 : 0.4,
            }}/>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, padding: '0 20px' }}>
        <div style={{ background: 'var(--card)', border: '1px solid var(--line)', padding: 20, borderRadius: 4 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
            {bar(70)}
            {bar(40)}
          </div>
          {bar('85%', 20)}
          <div style={{ height: 8 }}/>
          {bar('65%', 20)}
          <div style={{ height: 18 }}/>
          <div className="briefly-shimmer-thumb" style={{ height: 160, background: 'var(--paper-2)', borderRadius: 2, marginBottom: 16, border: '1px solid var(--line-soft)' }}/>
          {bar('100%')}
          <div style={{ height: 6 }}/>
          {bar('100%')}
          <div style={{ height: 6 }}/>
          {bar('80%')}
        </div>
        <div style={{ padding: '22px 0', textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10, fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink-2)' }}>
            <span className="briefly-dot" style={{ color: 'var(--accent)' }}>●</span>
            뉴스를 가져오고 있어요
          </div>
        </div>
      </div>
      <TabBar active="today"/>
      <HomeIndicator/>
    </div>
  );
};

// ─── Empty ─── No bookmarks
const EmptyState = () => {
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>북마크</span>
          <Icon name="search" size={20} color="var(--ink-4)"/>
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 40px' }}>
        {/* Editorial illustration — stacked papers */}
        <div style={{ position: 'relative', width: 120, height: 100, marginBottom: 28 }}>
          <div style={{ position: 'absolute', left: 14, top: 12, width: 92, height: 72, background: 'var(--paper-2)', border: '1px solid var(--line)', transform: 'rotate(-4deg)' }}/>
          <div style={{ position: 'absolute', left: 20, top: 6, width: 92, height: 72, background: 'var(--card)', border: '1px solid var(--line)', transform: 'rotate(3deg)', padding: 10 }}>
            <div style={{ height: 3, background: 'var(--line)', marginBottom: 5, width: '70%' }}/>
            <div style={{ height: 3, background: 'var(--line)', marginBottom: 5, width: '90%' }}/>
            <div style={{ height: 3, background: 'var(--line)', marginBottom: 5, width: '60%' }}/>
          </div>
          <div style={{ position: 'absolute', right: 0, bottom: -8, width: 36, height: 36, borderRadius: 999, background: 'var(--accent)', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
            <Icon name="bookmark" size={18} color="var(--paper)"/>
          </div>
        </div>
        <h2 style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', textAlign: 'center' }}>
          저장한 기사가 없어요
        </h2>
        <div style={{ height: 18 }}/>
        <p style={{ fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink-2)', textAlign: 'center', marginTop: 0, lineHeight: 1.7, wordBreak: 'keep-all' }}>
          기사 상단의 북마크 아이콘을 눌러<br/>나중에 다시 읽을 기사를 모아보세요.
        </p>
        <button style={{ marginTop: 32, minHeight: 48, padding: '12px 24px', background: 'var(--ink)', color: 'var(--paper)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>
          오늘의 브리핑 보러가기
        </button>
      </div>
      <HomeIndicator/>
    </div>
  );
};

// ─── Error ─── Simple, editorial
const ErrorState = () => {
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>오류</span>
          <span style={{ width: 22 }}/>
        </div>
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 40px' }}>
        {/* Editorial illustration — torn / disconnected paper */}
        <div style={{ position: 'relative', width: 120, height: 100, marginBottom: 28 }}>
          <div style={{ position: 'absolute', left: 14, top: 12, width: 92, height: 72, background: 'var(--paper-2)', border: '1px solid var(--line)', transform: 'rotate(-4deg)' }}/>
          <div style={{ position: 'absolute', left: 20, top: 6, width: 92, height: 72, background: 'var(--card)', border: '1px solid var(--line)', transform: 'rotate(3deg)', padding: 10, overflow: 'hidden' }}>
            <div style={{ height: 3, background: 'var(--line)', marginBottom: 5, width: '70%' }}/>
            <div style={{ height: 3, background: 'var(--line)', marginBottom: 5, width: '40%' }}/>
            <div style={{ position: 'absolute', left: -4, right: -4, top: '52%', borderTop: '2px dashed var(--line)' }}/>
          </div>
          <div style={{ position: 'absolute', right: 0, bottom: -8, width: 36, height: 36, borderRadius: 999, background: 'var(--accent)', color: 'var(--paper)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 900, color: 'var(--paper)', lineHeight: 1 }}>!</span>
          </div>
        </div>
        <h2 style={{ fontFamily: 'var(--serif)', fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em', textAlign: 'center', margin: 0 }}>
          오류가 발생했어요
        </h2>
        <div style={{ marginTop: 8, fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-4)', letterSpacing: '0.1em', textAlign: 'center' }}>
          ERR_NETWORK · 0x0A42
        </div>
        <p style={{ fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink-2)', textAlign: 'center', marginTop: 10, lineHeight: 1.7, wordBreak: 'keep-all' }}>
          잠시 후 다시 시도해 주세요.
        </p>
        <button style={{ marginTop: 32, minHeight: 48, padding: '12px 24px', background: 'var(--ink)', color: 'var(--paper)', border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 16, fontWeight: 600, cursor: 'pointer' }}>
          다시 시도
        </button>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.LoadingState = LoadingState;
window.EmptyState = EmptyState;
window.ErrorState = ErrorState;
