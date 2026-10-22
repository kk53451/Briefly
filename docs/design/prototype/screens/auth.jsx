// Auth screens — shown after tapping "시작하기" on the login screen.
// Two variants:
//   A — bottom sheet (default; keeps masthead visible behind)
//   B — full-screen login (traditional pattern)

// ─── Social login button, brand-styled ───
const SocialButton = ({ brand, label, note }) => {
  const styles = {
    kakao: { bg: '#FEE500', fg: '#1a1a1a', border: 'transparent' },
    google: { bg: '#FFFFFF', fg: '#1f1f1f', border: '#dadce0' },
    apple: { bg: '#000000', fg: '#FFFFFF', border: 'transparent' },
  }[brand];
  return (
    <button style={{
      width: '100%', height: 52, background: styles.bg, color: styles.fg,
      border: `1px solid ${styles.border}`, borderRadius: 4,
      fontFamily: 'var(--sans)', fontSize: 15, fontWeight: 600, cursor: 'pointer',
      display: 'flex', alignItems: 'center', position: 'relative', padding: '0 16px',
      letterSpacing: '-0.01em',
    }}>
      <BrandIcon name={brand} size={20} color={brand === 'apple' ? '#FFFFFF' : undefined}/>
      <span style={{ position: 'absolute', left: 0, right: 0, textAlign: 'center', pointerEvents: 'none' }}>
        {label}
      </span>
      {note && (
        <span style={{
          position: 'absolute', right: 14, top: -8,
          background: 'var(--accent)', color: 'var(--paper)',
          fontSize: 12, fontWeight: 700, letterSpacing: '0.06em',
          padding: '3px 8px', borderRadius: 2,
          fontFamily: 'var(--mono)',
        }}>{note}</span>
      )}
    </button>
  );
};

// ─── Legal microcopy ───
const LegalNote = () => (
  <div style={{
    fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)',
    textAlign: 'center', lineHeight: 1.6, letterSpacing: '-0.005em',
  }}>
    계속하면 <u style={{ textUnderlineOffset: 3 }}>서비스 이용약관</u>과<br/>
    <u style={{ textUnderlineOffset: 3 }}>개인정보 처리방침</u>에 동의하게 됩니다.
  </div>
);

// ─── A: Bottom sheet overlaid on masthead ───
const AuthSheet = () => {
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <StatusBarLite/>

      {/* Dimmed masthead behind sheet */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '40px 28px 0', opacity: 0.35, pointerEvents: 'none' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', marginTop: -40 }}>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 82, fontWeight: 900, lineHeight: 0.92, letterSpacing: '-0.04em', color: 'var(--ink)' }}>
            Briefly<span style={{ color: 'var(--accent)' }}>.</span>
          </div>
          <div style={{ fontFamily: 'var(--serif)', fontSize: 26, color: 'var(--ink-2)', marginTop: 58, lineHeight: 1.3, letterSpacing: '-0.01em', wordBreak: 'keep-all' }}>
            목소리로 편하게 듣는<br/>오늘의 헤드라인
          </div>
        </div>
      </div>

      {/* Scrim */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(26,23,20,0.25)', pointerEvents: 'none' }}/>

      {/* Sheet */}
      <div style={{
        position: 'absolute', left: 0, right: 0, bottom: 0,
        background: 'var(--paper)',
        borderTopLeftRadius: 20, borderTopRightRadius: 20,
        padding: '14px 28px 28px',
        boxShadow: '0 -20px 60px rgba(0,0,0,0.2)',
        borderTop: '3px solid var(--ink)',
      }}>
        {/* Drag handle */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
          <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--ink-3)', opacity: 0.4 }}/>
        </div>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div style={{ fontFamily: 'var(--label)', fontSize: 12, color: 'var(--ink-3)', marginBottom: 8 }}>SIGN IN</div>
          <h2 style={{ fontFamily: 'var(--serif)', fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--ink)', lineHeight: 1.2, wordBreak: 'keep-all' }}>
            계정으로 시작하기
          </h2>
          <p style={{ fontFamily: 'var(--serif)', fontSize: 14, color: 'var(--ink-2)', marginTop: 6, letterSpacing: '-0.01em' }}>
            관심 카테고리가 기기 간 동기화됩니다.
          </p>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 18 }}>
          <SocialButton brand="kakao" label="카카오로 시작하기"/>
          <SocialButton brand="google" label="Google로 시작하기"/>
          <SocialButton brand="apple" label="Apple로 시작하기"/>
        </div>

        {/* Guest fallback */}
        <button style={{
          width: '100%', padding: '10px', background: 'transparent',
          border: 0, fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--ink-3)',
          cursor: 'pointer', textDecoration: 'underline', textUnderlineOffset: 4,
          marginBottom: 14,
        }}>
          지금은 게스트로 둘러보기
        </button>

        <LegalNote/>
      </div>

      <HomeIndicator/>
    </div>
  );
};

// ─── B: Full-screen login ───
const AuthFull = () => {
  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>

      {/* Top bar with back */}
      <div style={{ padding: '8px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button style={{ background: 'transparent', border: 0, padding: 8, cursor: 'pointer', display: 'flex' }}>
          <Icon name="arrow-left" size={22}/>
        </button>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.2em', color: 'var(--ink-3)' }}>SIGN IN</span>
        <div style={{ width: 38 }}/>
      </div>

      {/* Masthead rule */}
      <div style={{ padding: '0 28px' }}>
        <div style={{ borderTop: '2px solid var(--ink)', marginTop: 6 }}/>
      </div>

      {/* Header block */}
      <div style={{ padding: '36px 28px 30px' }}>
        <div style={{ fontFamily: 'var(--serif)', fontSize: 44, fontWeight: 900, lineHeight: 1.02, letterSpacing: '-0.035em', color: 'var(--ink)', wordBreak: 'keep-all' }}>
          환영합니다<span style={{ color: 'var(--accent)' }}>.</span>
        </div>
        <div style={{ fontFamily: 'var(--serif)', fontSize: 16, color: 'var(--ink-2)', marginTop: 10, lineHeight: 1.5, letterSpacing: '-0.01em', wordBreak: 'keep-all' }}>
          1분이면 설정이 끝나요.<br/>
          자주 쓰는 계정으로 로그인하세요.
        </div>
      </div>

      {/* Buttons */}
      <div style={{ padding: '0 28px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        <SocialButton brand="kakao" label="카카오로 시작하기"/>
        <SocialButton brand="google" label="Google로 시작하기"/>
        <SocialButton brand="apple" label="Apple로 시작하기"/>
      </div>

      {/* OR divider */}
      <div style={{ padding: '22px 28px 14px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1, height: 1, background: 'var(--ink-3)', opacity: 0.3 }}/>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: '0.2em', color: 'var(--ink-3)' }}>OR</span>
        <div style={{ flex: 1, height: 1, background: 'var(--ink-3)', opacity: 0.3 }}/>
      </div>

      <div style={{ padding: '0 28px', textAlign: 'center' }}>
        <button style={{
          width: '100%', padding: '14px', background: 'transparent',
          border: '1px solid var(--ink)', borderRadius: 4,
          fontFamily: 'var(--sans)', fontSize: 14, fontWeight: 600, color: 'var(--ink)',
          cursor: 'pointer', letterSpacing: '-0.01em',
        }}>
          게스트로 둘러보기
        </button>
      </div>

      {/* Footer */}
      <div style={{ flex: 1 }}/>
      <div style={{ padding: '0 28px 24px' }}>
        <LegalNote/>
      </div>

      <HomeIndicator/>
    </div>
  );
};

window.AuthSheet = AuthSheet;
window.AuthFull = AuthFull;
