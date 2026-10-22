// Login screen — editorial masthead

// Rotating headline ticker — types a headline, holds, erases, moves to next.
// Shuffles every cycle so the order isn't predictable.
const useHeadlineTicker = (headlines, {
  typeSpeed = 70,
  eraseSpeed = 28,
  holdMs = 1400,
  gapMs = 400,
} = {}) => {
  const [idx, setIdx] = React.useState(0);
  const [text, setText] = React.useState('');
  const [phase, setPhase] = React.useState('typing'); // typing | holding | erasing | gap

  React.useEffect(() => {
    const current = headlines[idx % headlines.length];
    let timer;
    if (phase === 'typing') {
      if (text.length < current.length) {
        timer = setTimeout(() => setText(current.slice(0, text.length + 1)), typeSpeed);
      } else {
        timer = setTimeout(() => setPhase('holding'), 0);
      }
    } else if (phase === 'holding') {
      timer = setTimeout(() => setPhase('erasing'), holdMs);
    } else if (phase === 'erasing') {
      if (text.length > 0) {
        timer = setTimeout(() => setText(current.slice(0, text.length - 1)), eraseSpeed);
      } else {
        timer = setTimeout(() => setPhase('gap'), 0);
      }
    } else if (phase === 'gap') {
      timer = setTimeout(() => {
        setIdx(i => i + 1);
        setPhase('typing');
      }, gapMs);
    }
    return () => clearTimeout(timer);
  }, [text, phase, idx, headlines, typeSpeed, eraseSpeed, holdMs, gapMs]);

  return { text, phase };
};

const SAMPLE_HEADLINES = [
  '지방 경선결과 진행상황',
  '미국-이란 전쟁 상황',
  '동물원 늑대 탈출',
  '다주택자 과세율 변동',
  '유가 상승에 따른 물가',
  '서울시 민원 폭탄',
  'AI 규제 법안 국회 통과',
  '전국 기온 급강하 주의보',
  '코스피 3,200선 안착',
  '반도체 수출 호조',
];

const LoginScreen = ({ variant = 'A' }) => {
  if (variant === 'A') {
    // Editorial masthead, serif huge, cream paper
    const { text: tickerText, phase } = useHeadlineTicker(SAMPLE_HEADLINES);
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite/>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '40px 28px 24px' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', marginTop: -40 }}>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 82, fontWeight: 900, lineHeight: 0.92, letterSpacing: '-0.04em', color: 'var(--ink)' }}>
              Briefly<span style={{ color: 'var(--accent)' }}>.</span>
            </div>

            {/* Rotating headline ticker — "오늘 이런 뉴스가 있어요" 느낌 */}
            <div style={{ marginTop: 44, display: 'flex', alignItems: 'center', gap: 10, minHeight: 22 }}>
              {/* Live dot */}
              <div style={{
                width: 7, height: 7, borderRadius: '50%', background: 'var(--accent)',
                animation: 'brieflyLiveDot 1.2s ease-in-out infinite',
                flexShrink: 0,
              }}/>
              <div style={{
                fontFamily: 'var(--serif)', fontSize: 22,
                color: 'var(--ink-2)', letterSpacing: '-0.01em',
                whiteSpace: 'nowrap', overflow: 'hidden', lineHeight: 1.3,
              }}>
                {tickerText}
                <span style={{
                  display: 'inline-block', width: 2, height: '0.95em', background: 'var(--ink)',
                  marginLeft: 2, verticalAlign: '-0.12em',
                  animation: 'brieflyCaret 0.85s step-end infinite',
                }}/>
              </div>
            </div>

            {/* Static tagline */}
            <div style={{
              fontFamily: 'var(--serif)', fontSize: 26, color: 'var(--ink-2)',
              marginTop: 14, lineHeight: 1.3, letterSpacing: '-0.01em', wordBreak: 'keep-all',
            }}>
              목소리로 편하게 듣는<br/>오늘의 헤드라인
            </div>

            <style>{`
              @keyframes brieflyCaret { 50% { opacity: 0; } }
              @keyframes brieflyLiveDot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.35; transform: scale(0.8); } }
            `}</style>
          </div>

          {/* CTA */}
          <div>
            <button style={{
              width: '100%', padding: '18px', background: 'var(--ink)', color: 'var(--paper)',
              border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 600,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer',
            }}>
              시작하기 <Icon name="arrow-left" size={18} color="var(--paper)" /* flipped via transform */ />
            </button>
          </div>
        </div>
        <HomeIndicator/>
      </div>
    );
  }

  if (variant === 'B') {
    // Warm photo feature — placeholder image, overlay text
    return (
      <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--ink)', display: 'flex', flexDirection: 'column' }}>
        <StatusBarLite dark/>
        <div style={{ flex: 1, position: 'relative' }}>
          {/* Photo area */}
          <div style={{ position: 'absolute', inset: 0, background: `
            radial-gradient(ellipse at 30% 30%, #c9a87f33 0%, transparent 50%),
            radial-gradient(ellipse at 70% 80%, #a03a2855 0%, transparent 60%),
            repeating-linear-gradient(45deg, #2a2420 0 3px, #1a1714 3px 6px)
          ` }}/>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '24px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '1px solid rgba(247,242,233,0.15)' }}>
            <span style={{ fontFamily: 'var(--serif)', fontWeight: 700, fontSize: 20, color: 'var(--paper)' }}>Briefly<span style={{ color: '#d97654' }}>.</span></span>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.08em', color: '#b8ad9d' }}>2026. 4. 18.</span>
          </div>

          <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '36px 28px 24px' }}>
            <h1 style={{ fontFamily: 'var(--serif)', fontSize: 40, fontWeight: 700, color: 'var(--paper)', lineHeight: 1.08, letterSpacing: '-0.03em' }}>
              듣는 신문,<br/>하루 두 번.
            </h1>
            <p style={{ fontFamily: 'var(--serif)', fontSize: 16, color: '#d6c9b0', marginTop: 16, lineHeight: 1.5 }}>
              출근길, 퇴근길. <br/>오늘 놓치면 안 될 이슈를 앵커가 들려드립니다.
            </p>

            <button style={{
              width: '100%', padding: '18px', marginTop: 28, background: '#d97654', color: 'var(--ink)',
              border: 0, borderRadius: 2, fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 700, cursor: 'pointer',
              letterSpacing: '0.02em',
            }}>
              오늘의 브리핑 듣기
            </button>
          </div>
        </div>
        <HomeIndicator/>
      </div>
    );
  }

  // C — minimal literary cover
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper-2)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '60px 32px 24px', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, justifyContent: 'center', marginBottom: 28 }}>
            <div style={{ width: 40, height: 1, background: 'var(--ink-3)' }}/>
            <div style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink-3)' }}>2026년</div>
            <div style={{ width: 40, height: 1, background: 'var(--ink-3)' }}/>
          </div>
          <h1 style={{ fontFamily: 'var(--serif)', fontSize: 72, fontWeight: 900, lineHeight: 0.95, letterSpacing: '-0.04em', color: 'var(--ink)' }}>
            Briefly
          </h1>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 17, color: 'var(--ink-2)', marginTop: 28, lineHeight: 1.5 }}>
            “하루의 소음 속에서<br/>정말 중요한 여섯 가지.”
          </div>
        </div>
      </div>
      <div style={{ padding: '0 32px 24px' }}>
        <button style={{
          width: '100%', padding: '18px', background: 'var(--accent)', color: 'var(--paper)',
          border: 0, borderRadius: 999, fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 600, cursor: 'pointer',
        }}>
          오늘의 브리핑 열기
        </button>
      </div>
      <HomeIndicator/>
    </div>
  );
};

window.LoginScreen = LoginScreen;
