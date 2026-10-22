// Briefly mock data — realistic Korean news style
// Today: Friday April 18, 2026

const CATEGORIES = [
  { id: 'politics', ko: '정치',    color: '#B54A3A', icon: 'building' },
  { id: 'economy',  ko: '경제',    color: '#4A7C59', icon: 'trending' },
  { id: 'society',  ko: '사회',    color: '#6B4E8A', icon: 'people' },
  { id: 'culture',  ko: '문화',    color: '#B85A75', icon: 'palette' },
  { id: 'world',    ko: '국제',    color: '#3D6B8C', icon: 'globe' },
  { id: 'local',    ko: '지역',    color: '#C08A3E', icon: 'pin' },
  { id: 'tech',     ko: 'IT/과학', color: '#5A5FB0', icon: 'chip' },
];

const CAT_BY_ID = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));

// ── Today briefing (AM slot) — 6 topics
const BRIEFING_AM = [
  {
    topic_id: 0,
    category: 'economy',
    headline: '한은, 기준금리 또 올렸어요 — 연 3.75%로',
    summary: '한국은행이 오늘 새벽 기준금리를 0.25%p 인상했어요. 물가 상승 압력이 여전히 크다는 판단이에요. 시장은 이미 예상했던 수준이라 원·달러 환율은 소폭 내렸고, 주택담보대출 변동금리는 다음 주부터 오를 전망이에요.',
    cluster_size: 47,
    representative_title: '한국은행, 기준금리 3.75%로 0.25%p 인상…"물가 둔화 더딘 탓"',
    representative_press: '연합뉴스',
    keywords: ['기준금리', '한은', '물가', '가계부채'],
  },
  {
    topic_id: 1,
    category: 'politics',
    headline: '여야, 추경 35조 처리 합의 — 오늘 본회의',
    summary: '여야 원내대표가 35조원 규모 추가경정예산안 처리에 극적으로 합의했어요. 소상공인 지원과 반도체 R&D 예산이 핵심이에요. 오늘 오후 본회의에서 처리될 예정이고, 정부는 다음 주 중 집행에 착수해요.',
    cluster_size: 32,
    representative_title: '추경 35조 합의…여야 원내대표 "민생이 먼저"',
    representative_press: 'KBS',
    keywords: ['추경', '본회의', '소상공인', '반도체'],
  },
  {
    topic_id: 2,
    category: 'society',
    headline: '수도권 전세사기 피해자 특별법, 내달 1일 시행',
    summary: '전세사기 피해자 특별법이 5월 1일부터 시행돼요. 피해자로 인정되면 경매 우선매수권과 저금리 대환대출을 받을 수 있어요. 국토부는 전국 피해자 규모를 약 2만 8천명으로 추산했어요.',
    cluster_size: 21,
    representative_title: '전세사기 특별법 5월 1일 시행…2만8천명 구제 길',
    representative_press: '한겨레',
    keywords: ['전세사기', '특별법', '피해자', '경매'],
  },
  {
    topic_id: 3,
    category: 'world',
    headline: '미국 4월 CPI 2.4% — 금리 인하 기대 커져요',
    summary: '미국 4월 소비자물가지수가 전년 대비 2.4% 오르면서 예상을 밑돌았어요. 연준의 6월 금리 인하 가능성이 크게 높아졌고, 뉴욕증시는 사상 최고치를 경신했어요. 달러화는 주요 통화 대비 약세예요.',
    cluster_size: 28,
    representative_title: '美 CPI 2.4% 둔화…6월 금리인하 확률 72%',
    representative_press: '매일경제',
    keywords: ['CPI', '연준', '금리인하', '뉴욕증시'],
  },
  {
    topic_id: 4,
    category: 'tech',
    headline: '삼성전자, 2나노 양산 돌입 — TSMC와 정면승부',
    summary: '삼성전자 파운드리가 2나노 공정 양산을 공식 시작했어요. 첫 고객사는 엔비디아 차세대 AI칩으로 알려졌어요. 업계는 TSMC와의 기술 격차가 사실상 사라진 분기점으로 평가하고 있어요.',
    cluster_size: 19,
    representative_title: '삼성 2나노 양산 개시…"TSMC 추격 9부 능선"',
    representative_press: '조선일보',
    keywords: ['삼성전자', '파운드리', '2나노', 'TSMC', '엔비디아'],
  },
  {
    topic_id: 5,
    category: 'culture',
    headline: '칸 영화제 한국영화 3편 경쟁부문 초청',
    summary: '제79회 칸 영화제 공식 경쟁부문에 한국영화 3편이 동시 초청됐어요. 박찬욱 감독의 신작과 신예 감독 두 명의 작품이 포함돼요. 한국영화 황금종려상 수상 이후 최대 규모 진출이에요.',
    cluster_size: 14,
    representative_title: '칸 영화제 경쟁부문에 한국영화 3편…역대 최다',
    representative_press: '씨네21',
    keywords: ['칸영화제', '박찬욱', '경쟁부문', '황금종려상'],
  },
];

const BRIEFING_PM = [
  {
    topic_id: 0,
    category: 'economy',
    headline: '코스피 3,120선 마감 — 외국인 1조 2천억 순매수',
    summary: '코스피가 금리 인상 충격을 딛고 반등했어요. 외국인이 반도체 중심으로 1조 2천억원을 사들였고, 특히 삼성전자와 SK하이닉스가 강세였어요. 원·달러 환율은 1,315원까지 내려왔어요.',
    cluster_size: 38,
    representative_title: '코스피 외국인 순매수에 3,120 회복…반도체 주도',
    representative_press: '한국경제',
    keywords: ['코스피', '외국인', '반도체', '환율'],
  },
  {
    topic_id: 1,
    category: 'politics',
    headline: '추경 35조 본회의 통과 — 여야 합의 처리',
    summary: '35조원 추경안이 오후 본회의에서 가결됐어요. 찬성 248, 반대 12로 사실상 만장일치였어요. 소상공인 이자 지원 8조와 반도체 설비 투자 6조가 다음 달부터 집행돼요.',
    cluster_size: 29,
    representative_title: '추경 35조 본회의 통과…찬성 248표 압도적',
    representative_press: 'SBS',
    keywords: ['추경', '본회의', '가결', '소상공인'],
  },
  {
    topic_id: 2,
    category: 'society',
    headline: '서울 초미세먼지 \'매우나쁨\' — 주말까지 지속',
    summary: '수도권 초미세먼지 농도가 사흘째 \'매우나쁨\' 수준이에요. 중국발 황사와 국내 정체가 겹쳤어요. 환경부는 주말까지 고농도가 이어질 것으로 보고 야외활동 자제를 당부했어요.',
    cluster_size: 24,
    representative_title: '수도권 초미세먼지 \'매우나쁨\' 사흘째…주말도 계속',
    representative_press: 'JTBC',
    keywords: ['초미세먼지', '황사', '수도권', '환경부'],
  },
  {
    topic_id: 3,
    category: 'world',
    headline: '뉴욕증시 사상 최고 — S&P 5% 상승',
    summary: 'S&P 500 지수가 5,420선을 돌파하며 사상 최고치를 경신했어요. CPI 둔화에 금리 인하 기대가 더해진 결과예요. 나스닥도 AI 관련주 강세로 2.8% 올랐어요.',
    cluster_size: 22,
    representative_title: 'S&P 5,420 사상 최고…"금리인하 기대 반영"',
    representative_press: '이데일리',
    keywords: ['S&P', '나스닥', 'AI', '사상최고'],
  },
  {
    topic_id: 4,
    category: 'tech',
    headline: '오픈AI, GPT-6 공개 — 한국어 성능 대폭 향상',
    summary: '오픈AI가 GPT-6를 공개했어요. 추론 능력이 전작 대비 40% 개선됐고, 한국어 벤치마크에서 처음으로 GPT가 Gemini를 앞섰어요. 국내 스타트업들의 API 전환이 빨라질 전망이에요.',
    cluster_size: 15,
    representative_title: 'GPT-6 등장…"한국어 성능 Gemini 추월"',
    representative_press: '전자신문',
    keywords: ['GPT-6', '오픈AI', '한국어', 'Gemini'],
  },
];

// ── Home news cards (per category, ranked)
const NEWS_BY_CATEGORY = {
  economy: [
    { rank: 1, title: '한국은행, 기준금리 3.75%로 0.25%p 인상…물가 둔화 더뎌', provider: '연합뉴스', cluster_size: 47, published_at: '06:10' },
    { rank: 2, title: '원·달러 환율 1,315원…3주 만에 최저치 기록', provider: '매일경제', cluster_size: 22, published_at: '07:42' },
    { rank: 3, title: '코스피 3,100 회복…반도체·2차전지 동반 상승', provider: '한국경제', cluster_size: 19, published_at: '09:15' },
    { rank: 4, title: '주담대 변동금리, 다음 주부터 0.2%p 오른다', provider: 'KBS', cluster_size: 14, published_at: '08:30' },
    { rank: 5, title: '4월 소비자심리지수 98.4…넉 달 만에 반등', provider: '이데일리', cluster_size: 11, published_at: '10:00' },
    { rank: 6, title: '현대차 1분기 영업이익 4조 돌파…역대 최대', provider: '조선비즈', cluster_size: 9, published_at: '10:45' },
    { rank: 7, title: '건설 경기 넉 달째 하락…미분양 7만 호 육박', provider: '한겨레', cluster_size: 8, published_at: '11:20' },
  ],
  politics: [
    { rank: 1, title: '여야, 추경 35조 처리 합의…오늘 본회의 상정', provider: 'KBS', cluster_size: 32, published_at: '05:50' },
    { rank: 2, title: '대통령, 민생경제점검회의 주재…"집행 속도 높여야"', provider: '연합뉴스', cluster_size: 18, published_at: '09:00' },
    { rank: 3, title: '국정감사 일정 확정…9월 22일부터 20일간', provider: 'SBS', cluster_size: 13, published_at: '10:30' },
    { rank: 4, title: '민주당 지지율 34.2%…국민의힘과 4.1%p 차', provider: 'YTN', cluster_size: 11, published_at: '11:00' },
    { rank: 5, title: '방산비리 수사 본격화…전 국방부 고위 관계자 소환', provider: '한겨레', cluster_size: 8, published_at: '12:10' },
  ],
  society: [
    { rank: 1, title: '전세사기 특별법 5월 1일 시행…2만 8천명 구제', provider: '한겨레', cluster_size: 21, published_at: '07:00' },
    { rank: 2, title: '초미세먼지 \'매우나쁨\'…수도권 사흘째 고농도', provider: 'JTBC', cluster_size: 17, published_at: '08:20' },
    { rank: 3, title: '서울시, 청년월세 지원 대상 2만 명 확대', provider: '서울신문', cluster_size: 10, published_at: '09:40' },
    { rank: 4, title: '전국 곳곳 강풍주의보…강원 산불 경계 강화', provider: 'MBC', cluster_size: 9, published_at: '10:15' },
  ],
  world: [
    { rank: 1, title: '美 4월 CPI 2.4% 둔화…6월 금리인하 확률 72%', provider: '매일경제', cluster_size: 28, published_at: '06:30' },
    { rank: 2, title: 'S&P 500 사상 최고 5,420선 돌파', provider: '이데일리', cluster_size: 22, published_at: '07:05' },
    { rank: 3, title: '일본 엔화 152엔대…34년 만의 최저치', provider: '한국경제', cluster_size: 12, published_at: '09:20' },
    { rank: 4, title: '중국 1분기 GDP 4.8% 성장…예상 상회', provider: '연합뉴스', cluster_size: 10, published_at: '10:00' },
  ],
  tech: [
    { rank: 1, title: '삼성전자 2나노 양산 개시…TSMC 추격 9부 능선', provider: '조선일보', cluster_size: 19, published_at: '08:00' },
    { rank: 2, title: 'GPT-6 공개…"한국어 성능 Gemini 추월"', provider: '전자신문', cluster_size: 15, published_at: '10:30' },
    { rank: 3, title: 'LG엔솔, 전고체 배터리 시제품 공개', provider: '한국경제', cluster_size: 11, published_at: '11:15' },
    { rank: 4, title: '네이버, 검색 AI \'큐\' 글로벌 베타 시작', provider: '디지털타임스', cluster_size: 8, published_at: '12:00' },
  ],
  culture: [
    { rank: 1, title: '칸 영화제 경쟁부문 한국영화 3편…역대 최다', provider: '씨네21', cluster_size: 14, published_at: '09:30' },
    { rank: 2, title: 'BTS 지민 솔로앨범 빌보드 200 1위 데뷔', provider: '스포츠서울', cluster_size: 12, published_at: '10:45' },
    { rank: 3, title: '국립중앙박물관 고려청자 특별전, 30만 관람', provider: '한겨레', cluster_size: 7, published_at: '11:30' },
  ],
  local: [
    { rank: 1, title: '부산 엑스포 후속 사업 예산 1조 2천억 확보', provider: '부산일보', cluster_size: 8, published_at: '09:00' },
    { rank: 2, title: '제주 관광객 4월 150만…전년 대비 22% 증가', provider: '제주일보', cluster_size: 6, published_at: '10:20' },
  ],
};

// ── Podcast scripts (preview)
const SCRIPTS = {
  am: `앵커: 4월 18일 금요일 아침 브리플리입니다. 오늘 새벽 한국은행이 기준금리를 0.25%포인트 올렸습니다. 연 3.75%, 13년 만에 가장 높은 수준인데요.

해설: 시장에서는 이미 예상한 인상이었고요. 다만 한은이 성명에서 "근원물가 둔화가 더디다"고 한 대목이 중요합니다. 추가 인상 가능성을 완전히 닫지 않은 거죠.

앵커: 정치권도 움직입니다. 여야가 35조 추경안 처리에 합의했어요. 오늘 오후 본회의가 예정돼 있고요.

해설: 미국 4월 CPI도 2.4%로 둔화되면서 연준의 6월 금리 인하 가능성이 한층 커졌습니다...`,

  pm: `앵커: 4월 18일 금요일 저녁 브리플리입니다. 코스피가 3,120선을 회복했습니다. 외국인이 반도체 중심으로 1조 2천억을 순매수했어요.

해설: 오전 금리 인상 충격을 외국인 매수세가 완전히 상쇄한 하루였습니다. 원·달러 환율도 1,315원까지 내려왔고요.

앵커: 국회에서는 추경 35조가 결국 통과됐습니다. 찬성 248, 반대 12. 사실상 만장일치였어요...`,

  economy: `앵커: 오늘 새벽 한국은행이 기준금리를 0.25%포인트 올렸습니다. 이로써 연 3.75%가 됐는데요, 해설위원님, 시장에서는 예상했던 인상이죠?

해설: 네, 이미 지난달부터 선반영된 측면이 크고요. 문제는 앞으로입니다. 한은은 성명문에서 "근원물가 둔화가 더디다"고 표현했는데, 이건 추가 인상 가능성도 완전히 닫지 않았다는 뜻으로 읽힙니다.

앵커: 가계부채 영향은 어떨까요?

해설: 변동금리 주담대 이용자들은 다음 주부터 월 이자가 평균 2만 원 정도 더 늘어날 것으로 보입니다. 신규 대출 수요는 당분간 위축될 가능성이 높고요...`,

  politics: `앵커: 드디어 여야가 추가경정예산안에 합의했습니다. 규모는 35조 원, 오늘 오후 본회의에 상정됩니다.

해설: 예상보다 빠른 합의였습니다. 핵심은 소상공인 이자 지원 8조와 반도체 설비 투자 6조인데요, 양당 모두 민생과 미래 먹거리라는 명분에서 물러서기 어려웠던 상황입니다...`,
};

// ── Podcast episode history (하루 2회: 오전/오후, 최근 순)
const PODCAST_EPISODES = [
  { id: 'ep-0418-pm', date: '4. 18.', dateKo: '4월 18일', day: '금', slot: 'PM', slotKo: '오후', subtitle: '코스피 3,120 회복, 추경 통과, GPT-6', duration: '5:12', status: 'upcoming', listens: 0, scriptKey: 'pm' },
  { id: 'ep-0418-am', date: '4. 18.', dateKo: '4월 18일', day: '금', slot: 'AM', slotKo: '오전', subtitle: '금리 3.75% 인상, 추경 35조 합의, 美 CPI 둔화', duration: '4:58', status: 'playing', listens: 1248, scriptKey: 'am' },
  { id: 'ep-0417-pm', date: '4. 17.', dateKo: '4월 17일', day: '목', slot: 'PM', slotKo: '오후', subtitle: '반도체 수출 2년 만에 최대, 美 연준 의사록', duration: '5:22', status: 'listened', listens: 8924, scriptKey: 'pm' },
  { id: 'ep-0417-am', date: '4. 17.', dateKo: '4월 17일', day: '목', slot: 'AM', slotKo: '오전', subtitle: '전세사기 특별법 시행 확정, 삼성 2나노 발표', duration: '4:40', status: 'listened', listens: 9102, scriptKey: 'am' },
  { id: 'ep-0416-pm', date: '4. 16.', dateKo: '4월 16일', day: '수', slot: 'PM', slotKo: '오후', subtitle: '코스피 외국인 순매수 반등, 유가 급등', duration: '4:50', status: 'listened', listens: 8512, scriptKey: 'pm' },
  { id: 'ep-0416-am', date: '4. 16.', dateKo: '4월 16일', day: '수', slot: 'AM', slotKo: '오전', subtitle: '4월 수출 통계, 일본 엔화 34년 만 최저', duration: '5:05', status: 'listened', listens: 8876, scriptKey: 'am' },
  { id: 'ep-0415-pm', date: '4. 15.', dateKo: '4월 15일', day: '화', slot: 'PM', slotKo: '오후', subtitle: '국감 일정 확정, 서울시 청년월세 확대', duration: '4:48', status: 'listened', listens: 8210, scriptKey: 'pm' },
  { id: 'ep-0415-am', date: '4. 15.', dateKo: '4월 15일', day: '화', slot: 'AM', slotKo: '오전', subtitle: 'BTS 지민 빌보드 1위, 칸 영화제 초청 3편', duration: '4:32', status: 'listened', listens: 8654, scriptKey: 'am' },
];

// ── helpers
const todayKorean = '4월 18일 금요일';
const now = { am: true }; // default slot

window.BRIEFLY = {
  CATEGORIES, CAT_BY_ID,
  BRIEFING_AM, BRIEFING_PM,
  NEWS_BY_CATEGORY,
  SCRIPTS,
  PODCAST_EPISODES,
  todayKorean,
};
