// 폰트 설정 화면 — 제목/본문 폰트를 드롭다운으로 선택하고 실시간 프리뷰
const FontSettingsScreen = () => {
  const SERIF_OPTS = [
    { id: 'noto-serif', name: 'Noto Serif KR', stack: "'Noto Serif KR', serif", weight: 700 },
    { id: 'nanum-myeongjo', name: 'Nanum Myeongjo', stack: "'Nanum Myeongjo', serif", weight: 700 },
    { id: 'gowun-batang', name: 'Gowun Batang', stack: "'Gowun Batang', serif", weight: 700 },
    { id: 'noto-serif-bold', name: 'Noto Serif KR Black', stack: "'Noto Serif KR', serif", weight: 900 },
  ];
  const SANS_OPTS = [
    { id: 'pretendard', name: 'Pretendard', stack: "'Pretendard', 'Pretendard Variable', sans-serif", weight: 500 },
    { id: 'noto-sans', name: 'Noto Sans KR', stack: "'Noto Sans KR', sans-serif", weight: 500 },
    { id: 'ibm-plex-sans', name: 'IBM Plex Sans KR', stack: "'IBM Plex Sans KR', sans-serif", weight: 500 },
    { id: 'gowun-dodum', name: 'Gowun Dodum', stack: "'Gowun Dodum', sans-serif", weight: 400 },
  ];

  // 현재 적용된 값(원본) vs 편집 중인 값
  const SIZE_OPTS = [
    { id: 'sm',  label: '작게',     mult: 0.92 },
    { id: 'md',  label: '보통',     mult: 1.00 },
    { id: 'lg',  label: '크게',     mult: 1.12 },
    { id: 'xl',  label: '아주 크게', mult: 1.24 },
  ];

  const [applied, setApplied] = React.useState({ serif: 'noto-serif', sans: 'pretendard', size: 'md' });
  const [draft, setDraft] = React.useState({ serif: 'noto-serif', sans: 'pretendard', size: 'md' });
  const [openDropdown, setOpenDropdown] = React.useState(null); // 'serif' | 'sans' | null

  const dirty = draft.serif !== applied.serif || draft.sans !== applied.sans || draft.size !== applied.size;
  const draftSerif = SERIF_OPTS.find(o => o.id === draft.serif);
  const draftSans = SANS_OPTS.find(o => o.id === draft.sans);
  const draftSize = SIZE_OPTS.find(o => o.id === draft.size);
  const sizeMult = draftSize.mult;

  const reset = () => { setDraft(applied); setOpenDropdown(null); };
  const apply = () => { setApplied(draft); setOpenDropdown(null); };

  return (
    <div className="briefly" style={{ width: '100%', height: '100%', background: 'var(--paper)', display: 'flex', flexDirection: 'column' }}>
      <StatusBarLite/>

      {/* Top bar — Type B 표준 */}
      <div style={{ padding: '14px 24px 12px', borderBottom: '2px solid var(--ink)', background: 'var(--paper)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Icon name="arrow-left" size={22}/>
          <span style={{ fontFamily: 'var(--serif)', fontSize: 17, fontWeight: 900, letterSpacing: '-0.02em' }}>폰트 설정</span>
          {dirty ? (
            <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', letterSpacing: '0.14em', textTransform: 'uppercase' }}>• 변경됨</span>
          ) : (
            <span style={{ width: 22 }}/>
          )}
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }} onClick={() => setOpenDropdown(null)}>
        {/* ─── PREVIEW ─── */}
        <div style={{ background: 'var(--paper-2)', borderBottom: '1px solid var(--line)', padding: '16px 20px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.14em', fontWeight: 600 }}>미리보기</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-4)', letterSpacing: '0.08em' }}>
              {draftSerif.name.replace(/ KR$/, '')} / {draftSans.name.replace(/ KR$/, '')} · {draftSize.label}
            </div>
          </div>

          {/* 신문 카드 */}
          <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', padding: '16px 16px 18px' }}>
            <div style={{ fontFamily: draftSans.stack, fontSize: 12, color: 'var(--accent)', letterSpacing: '0.18em', textTransform: 'uppercase', fontWeight: 600, marginBottom: 6 }}>
              경제 · 4월 25일
            </div>
            <div style={{ fontFamily: draftSerif.stack, fontWeight: draftSerif.weight, fontSize: 22 * sizeMult, lineHeight: 1.28, letterSpacing: '-0.025em', color: 'var(--ink)', marginBottom: 8 }}>
              한은 기준금리 동결, 시장은 “하반기 인하” 가능성에 무게
            </div>
            <div style={{ fontFamily: draftSans.stack, fontWeight: draftSans.weight, fontSize: 13 * sizeMult, lineHeight: 1.65, color: 'var(--ink-2)', letterSpacing: '-0.005em' }}>
              한국은행 금융통화위원회가 기준금리를 연 3.50%로 다섯 차례 연속 동결했다. 다만 의사록에서 일부 위원들이
              물가 둔화세를 근거로 연내 인하 가능성을 시사하면서 시장은 7월 회의를 주목하고 있다.
            </div>
          </div>

          {/* 작은 라벨 */}
          <div style={{ display: 'flex', gap: 16, marginTop: 10, fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.1em' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, background: 'var(--accent)', display: 'inline-block' }}/>
              <span>제목</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 8, height: 8, background: 'var(--ink-3)', display: 'inline-block' }}/>
              <span>본문</span>
            </div>
          </div>
        </div>

        {/* ─── 드롭다운 영역 ─── */}
        <div style={{ padding: '20px 20px 24px' }}>
          <FontDropdown
            label="제목 폰트"
            options={SERIF_OPTS}
            value={draft.serif}
            isOpen={openDropdown === 'serif'}
            onToggle={(e) => { e.stopPropagation(); setOpenDropdown(openDropdown === 'serif' ? null : 'serif'); }}
            onChange={(id) => { setDraft({ ...draft, serif: id }); setOpenDropdown(null); }}
            renderSample={(opt, size) => (
              <span style={{ fontFamily: opt.stack, fontWeight: opt.weight, fontSize: size, letterSpacing: '-0.025em', lineHeight: 1.2 }}>
                제목은 신문처럼
              </span>
            )}
            previewSize={20}
            optionSampleSize={18}
          />

          <div style={{ height: 14 }}/>

          <FontDropdown
            label="본문 폰트"
            options={SANS_OPTS}
            value={draft.sans}
            isOpen={openDropdown === 'sans'}
            onToggle={(e) => { e.stopPropagation(); setOpenDropdown(openDropdown === 'sans' ? null : 'sans'); }}
            onChange={(id) => { setDraft({ ...draft, sans: id }); setOpenDropdown(null); }}
            renderSample={(opt, size) => (
              <span style={{ fontFamily: opt.stack, fontWeight: opt.weight, fontSize: size, lineHeight: 1.5, letterSpacing: '-0.005em' }}>
                본문은 읽기 좋게 가나다 ABC 0123
              </span>
            )}
            previewSize={14}
            optionSampleSize={13}
          />

          <div style={{ height: 22 }}/>

          {/* ─── 글자 크기 ─── */}
          <div onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 8 }}>
              <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, letterSpacing: '-0.01em' }}>글자 크기</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--ink-4)', letterSpacing: '0.1em' }}>{Math.round(sizeMult * 100)}%</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', border: '1px solid var(--line)', background: 'var(--paper)' }}>
              {SIZE_OPTS.map((opt, i) => {
                const selected = draft.size === opt.id;
                return (
                  <div
                    key={opt.id}
                    onClick={() => setDraft({ ...draft, size: opt.id })}
                    style={{
                      padding: '12px 0 14px',
                      cursor: 'pointer',
                      borderRight: i < SIZE_OPTS.length - 1 ? '1px solid var(--line)' : 'none',
                      background: selected ? 'var(--ink)' : 'transparent',
                      color: selected ? 'var(--paper)' : 'var(--ink-2)',
                      transition: 'background 120ms ease',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                    }}>
                    <span style={{ fontFamily: 'var(--serif)', fontWeight: selected ? 900 : 700, fontSize: 12 + (i * 3), letterSpacing: '-0.02em', lineHeight: 1 }}>가</span>
                    <span style={{ fontFamily: 'var(--sans)', fontSize: 11, fontWeight: selected ? 700 : 500, letterSpacing: '-0.005em' }}>{opt.label}</span>
                  </div>
                );
              })}
            </div>
            <div style={{ fontFamily: 'var(--sans)', fontSize: 11.5, color: 'var(--ink-3)', marginTop: 8, lineHeight: 1.5 }}>
              제목과 본문 글자가 동시에 조절됩니다. 이야기에서 미리보기를 확인하세요.
            </div>
          </div>
        </div>

        <div style={{ height: 80 }}/>
      </div>

      {/* ─── 하단 액션 ─── */}
      <div style={{
        borderTop: '1px solid var(--line)',
        background: 'var(--paper)',
        padding: '12px 20px 14px',
        display: 'flex',
        gap: 10,
      }}>
        <button
          onClick={reset}
          disabled={!dirty}
          style={{
            flex: '0 0 38%',
            padding: '13px 0',
            background: 'transparent',
            color: dirty ? 'var(--ink)' : 'var(--ink-4)',
            border: '1px solid var(--line)',
            borderRadius: 2,
            fontFamily: 'var(--sans)',
            fontSize: 13.5,
            fontWeight: 600,
            cursor: dirty ? 'pointer' : 'default',
            letterSpacing: '-0.01em',
          }}>
          되돌리기
        </button>
        <button
          onClick={apply}
          disabled={!dirty}
          style={{
            flex: 1,
            padding: '13px 0',
            background: dirty ? 'var(--ink)' : 'var(--line)',
            color: dirty ? 'var(--paper)' : 'var(--ink-4)',
            border: 0,
            borderRadius: 2,
            fontFamily: 'var(--sans)',
            fontSize: 13.5,
            fontWeight: 700,
            cursor: dirty ? 'pointer' : 'default',
            letterSpacing: '-0.01em',
          }}>
          {dirty ? '적용하기' : '적용됨'}
        </button>
      </div>
      <HomeIndicator/>
    </div>
  );
};

// 드롭다운 — 라벨 + 현재값 헤더, 클릭 시 옵션 패널 펼침
const FontDropdown = ({ label, options, value, isOpen, onToggle, onChange, renderSample, previewSize, optionSampleSize }) => {
  const current = options.find(o => o.id === value);
  return (
    <div>
      <div style={{ fontFamily: 'var(--serif)', fontSize: 16, fontWeight: 700, letterSpacing: '-0.01em', marginBottom: 8 }}>{label}</div>

      {/* 헤더 — 현재 선택된 폰트로 렌더된 이름 + 샘플 */}
      <div
        onClick={onToggle}
        style={{
          border: isOpen ? '2px solid var(--ink)' : '1px solid var(--line)',
          background: 'var(--paper)',
          padding: isOpen ? '13px 14px' : '14px 15px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          transition: 'all 120ms ease',
        }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.06em', marginBottom: 4, textTransform: 'uppercase' }}>
            {current.name}
          </div>
          <div style={{ color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {renderSample(current, previewSize)}
          </div>
        </div>
        <div style={{
          transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 160ms ease',
          color: 'var(--ink-3)',
          display: 'flex',
        }}>
          <Icon name="chevron-down" size={18} color="var(--ink-2)"/>
        </div>
      </div>

      {/* 펼친 옵션들 */}
      {isOpen && (
        <div style={{
          marginTop: 6,
          border: '1px solid var(--line)',
          background: 'var(--paper)',
          boxShadow: '0 6px 18px rgba(26,23,20,0.08)',
        }}
        onClick={(e) => e.stopPropagation()}>
          {options.map((opt, i) => {
            const selected = value === opt.id;
            return (
              <div
                key={opt.id}
                onClick={() => onChange(opt.id)}
                style={{
                  padding: '12px 15px',
                  borderBottom: i < options.length - 1 ? '1px solid var(--line-soft)' : 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  background: selected ? 'var(--paper-2)' : 'transparent',
                }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--sans)', fontSize: 12, fontWeight: selected ? 700 : 500, color: 'var(--ink)', marginBottom: 3 }}>
                    {opt.name}
                  </div>
                  <div style={{ color: 'var(--ink-2)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {renderSample(opt, optionSampleSize)}
                  </div>
                </div>
                {selected && (
                  <div style={{ color: 'var(--ink)', display: 'flex' }}>
                    <Icon name="check" size={16} color="var(--ink)"/>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

window.FontSettingsScreen = FontSettingsScreen;
