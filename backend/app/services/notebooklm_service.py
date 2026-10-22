"""
NotebookLM 팟캐스트 생성 서비스

notebooklm-py (비공식 API)를 사용하여 뉴스 토픽에서
한국어 대화형 팟캐스트를 생성합니다.

⚠️ 비공식 API — 프로덕션 사용 시 주의사항:
- 쿠키 만료 시 수동 재로그인 필요 (notebooklm login)
- Google ToS 리스크 (개인 프로젝트 수준에서는 현실적 위험 낮음)
- Lambda 불가 → 로컬 노트북에서만 실행
"""

import asyncio
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# TTS-safe 숫자 전처리
# ──────────────────────────────────────────────
#
# 실측: NotebookLM 이 "3,256만 명"을 "3,256명" 으로, "1만 40톤"을 "1만 4톤" 으로
# 잘못 발음하는 체계적 오류가 있음 (4/16 실험).
#
# 원인 가설: 대본에서 숫자와 단위가 공백 없이 붙어 있으면(`3256만명`) NotebookLM
# 내부 재작성 단계에서 토큰 경계가 모호해지고, 단위(만/억/조)가 드랍될 수 있음.
#
# 대응: 대본 → NotebookLM 전달 직전에 정규식으로 토큰 경계를 명시화.
#   1) 숫자 뒤 만/억/조 뒤에 공백 삽입 (다음 토큰이 숫자든 한글이든)
#   2) 만/억/조 앞 4자리 이상 숫자에 콤마 삽입
# 이것만으로는 100% 방어가 안 되므로 v2 instructions 에도 단위 보존 규칙을
# concrete example 과 함께 명시함 (벨트+멜빵).


def probe_audio_duration_seconds(path: str) -> Optional[int]:
    """오디오 파일의 재생 길이(초)를 추출합니다.

    NotebookLM 이 돌려주는 파일은 `.mp3` 확장자지만 **DASH-fragmented MP4**
    (ftyp=dash, AAC 스트림) 이라 mutagen MP4 파서가 `mvhd.duration` 을 찾지
    못하고 0 을 반환하는 케이스가 확인됐습니다 (2026-04-19 실측).

    그래서 우선순위:
    1. **ffprobe** — 실제 스트림을 디코딩해 정확한 duration 추출. 대부분의
       dev·서버 환경에 ffmpeg 가 이미 설치돼 있음.
    2. **mutagen** — ffprobe 미설치 환경의 fallback. DASH-MP4 를 만나면
       0 을 돌려줄 수 있으니 그 경우 None 으로 변환.

    Returns:
        반올림 정수 초. 둘 다 실패하거나 파일 이상 시 None.
    """
    if not path:
        return None

    from pathlib import Path as _Path
    try:
        p = _Path(path)
        if not p.exists() or p.stat().st_size < 1024:
            logger.warning(f"  ⏱️ duration probe skip — invalid file: {path}")
            return None
    except Exception as e:
        logger.warning(f"  ⏱️ duration probe path check 실패: {e}")
        return None

    # 1) ffprobe 우선
    import subprocess
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            value = (result.stdout or "").strip()
            if value:
                length = float(value)
                if length > 0:
                    return int(round(length))
    except FileNotFoundError:
        # ffprobe 미설치 — mutagen fallback 시도
        pass
    except subprocess.TimeoutExpired:
        logger.warning(f"  ⏱️ ffprobe 타임아웃(15s) — mutagen fallback")
    except Exception as e:
        logger.warning(f"  ⏱️ ffprobe 실패: {e} — mutagen fallback")

    # 2) mutagen fallback
    try:
        from mutagen import File as MutagenFile
    except ImportError:
        logger.warning(
            "  ⏱️ ffprobe·mutagen 둘 다 불가 — duration probe 생략"
        )
        return None

    try:
        mf = MutagenFile(path)
        if mf is None or not getattr(mf, "info", None):
            return None
        length = getattr(mf.info, "length", None)
        if length is None:
            return None
        rounded = int(round(float(length)))
        if rounded <= 0:
            # DASH-fragmented MP4 가 0 을 돌려주는 케이스 — None 으로 취급
            logger.warning(
                f"  ⏱️ mutagen fallback: length=0 (DASH-MP4 가능성) — None 반환"
            )
            return None
        return rounded
    except Exception as e:
        logger.warning(f"  ⏱️ mutagen fallback 실패: {e}")
        return None


def _strip_code_fence(text: str) -> str:
    """모델이 응답을 ``` 블록으로 감싸 저장된 경우 fence 제거.
    NotebookLM add_text 가 ``` 으로 시작하는 텍스트를 FAILED_PRECONDITION 으로 거절하므로
    엔진 단의 strip 이 누락된 과거 대본 파일에 대한 방어층.
    """
    s = text.strip()
    if not s.startswith("```"):
        return s
    lines = s.split("\n")
    if len(lines) < 2 or lines[-1].strip() != "```":
        return s
    return "\n".join(lines[1:-1]).strip()


def _tts_safe_numbers(text: str) -> str:
    """
    한국어 복합 숫자를 TTS 친화적 형태로 변환합니다.

    예시:
        3256만명   → 3,256만 명
        5억9701만원 → 5억 9,701만 원
        1만40톤     → 1만 40톤
        26조2000억원 → 26조 2,000억 원
        2027년      → 2027년 (변환 없음 - 만/억/조 없음)
        5,732건     → 5,732건 (변환 없음)

    Args:
        text: 원본 대본 텍스트

    Returns:
        숫자 경계가 명시화된 텍스트
    """
    if not text:
        return text

    # 1단계: 숫자+(만|억|조) 뒤에 공백 삽입
    #   - 다음 토큰이 숫자인 경우: `5억9` → `5억 9`
    text = re.sub(r"(\d)(만|억|조)(\d)", r"\1\2 \3", text)
    #   - 다음 토큰이 한글인 경우: `1만원` → `1만 원`, `0만명` → `0만 명`
    text = re.sub(r"(\d)(만|억|조)([가-힣])", r"\1\2 \3", text)

    # 2단계: (만|억|조) 앞 4자리 이상 숫자에 콤마 삽입
    #   - `3256만` → `3,256만`
    #   - `9701만` → `9,701만`
    #   - 2027년 처럼 만/억/조가 뒤에 없는 숫자는 건드리지 않음
    def _add_commas(m: "re.Match") -> str:
        num, unit = m.group(1), m.group(2)
        if len(num) >= 4:
            return f"{int(num):,}{unit}"
        return m.group(0)

    text = re.sub(r"(\d+)(만|억|조)", _add_commas, text)

    return text


# ──────────────────────────────────────────────
# NotebookLM 오디오 instructions
# ──────────────────────────────────────────────
#
# 이 instructions는 NotebookLM이 최종 오디오를 생성할 때의 "샤프한 가이드" 역할을
# 합니다. 대본(script_service.py SYSTEM_PROMPT)과 별개로, NotebookLM 내부 모델이
# 소스(대본 또는 원본 기사)를 자기 식으로 재해석하기 때문에 오디오 레이어에서도
# 톤·구조·금지 표현을 직접 지시해야 합니다.
#
# v1 (제거됨, 실측 4/14 script_adherence 2/5): 사실 충실도 5줄만 있어 톤 drift 발생.
# v2 (이전): 단일 카테고리 7분 브리핑용 — 정체성/진행자/금지표현/구조/사실/숫자 규정.
# v2 (현재): 통합 브리핑 리워크(2026-04-19) — 정치·경제·국제 3분야를 한 에피소드에
# 묶어 약 8~10분 진행 (2026-04-19 실측: 10~12분 지시로 20분39초 나와 분량 낮춤).
# 분야 간 전환 규칙과 오프닝·클로징 단일화 규정.
# 이전 v1 instructions 본문은 git history 에서 확인하세요.


INSTRUCTIONS_V2_TEMPLATE = """당신은 "Briefly"의 전문 한국어 뉴스 브리핑 오디오를 제작합니다.

## ⚠️ 0순위 절대 원칙 — 이 노트북의 [PRIMARY] 소스가 곧 대본입니다

이 에피소드의 모든 결정(쇼 이름, 토픽 선택, 토픽 순서, 톤, 분량, 오프닝·클로징,
화자 어조)은 **[PRIMARY] 로 표시된 단 하나의 소스**가 정합니다. [REF] 36건은
**대본에 이미 있는 사실의 출처 추적용 참고자료**일 뿐, 새로운 콘텐츠의 재료가
아닙니다.

**위계가 깨졌을 때 발생하는 사고 (2026-05-15 실측):**
NotebookLM 이 [PRIMARY] 대본(2,004자)을 무시하고 [REF] 36건을 가지고 자기 토크쇼
**"더 딥다이빙"** 을 만들어 9,411자(469%) 분량을 출력했습니다. 결과:
- 쇼 이름이 "Briefly" 가 아닌 "더 딥다이빙" 으로 변경됨 — **방송 정정 사안**
- 대본·소스 어디에도 없는 "하정우 후보 GRDP 1억 2천만 원 발언" 창작 — **명예훼손 위험**
- 대본에 없는 "AI vs 인간 투키디데스의 함정" 5분 분량 자유 철학 코멘터리 추가
- 12개 토픽 전체를 "주도권 쥐기 / 레버리지 극대화" 라는 단일 메타 서사로 재편 — **β-rule 토픽 독립 위반**
- 강남 아파트, 산소호흡기, 체스판, 틱톡댄스 등 비유·은유 도배 — **β-rule 비유 금지 위반**
- "여러분", "청취자 여러분" 호명 — 호명 금지 위반
- "황당한", "기이한", "치명적인", "허세" 등 평가어 도배 — 중립성 위반

**같은 사고를 반복하지 않기 위한 수술적 규칙:**

### 규칙 A — 쇼 이름 잠금
이 오디오의 쇼 이름은 **반드시 "Briefly"** 입니다. "더 딥다이빙", "딥다이브",
"오늘의 브리핑", "탐구 시간", 그 외 어떤 이름도 도입하지 마세요. 클로징은
PRIMARY 대본의 마지막 문장을 그대로 읽으세요.

### 규칙 B — 분량 잠금 (오버 생성 금지)
오디오 분량은 **PRIMARY 대본을 그대로 읽었을 때의 자연스러운 길이**에 맞춥니다.
대본이 짧으면 오디오도 짧게 끝내세요. 분량을 채우려고 [REF] 에서 새로운 토픽·
배경·일화를 끌어와 추가하는 것은 **절대 금지**입니다. NotebookLM 의 default
"긴 팟캐스트" 본능을 억누르세요. **대본보다 길어진 만큼이 곧 위반량입니다.**

### 규칙 C — 메타 서사 금지 (토픽 독립 원칙)
12 개 토픽을 하나의 큰 이야기로 묶지 마세요. "주도권 쥐기", "레버리지 극대화",
"체스판", "프레임 전쟁" 같은 모든 토픽을 관통하는 메타 서사를 도입하면 위반.
각 토픽은 독립적으로 다루고 카테고리 전환 시 PRIMARY 가 쓰는 짧은 brige
(예: "이제 경제 소식입니다") 만 허용됩니다.

### 규칙 D — 비유·은유 전면 금지
강남 아파트, 산소호흡기, 체스판, 틱톡댄스, 도시락통, 스파게티, 벙커, 거래,
은행장 앞 허세 — **이런 종류의 비유·은유·일화 비교는 단 한 개도 안 됩니다.**
사실은 사실 그대로 전달하세요.

### 규칙 E — 청취자 호명 금지
"여러분", "청취자 여러분", "지금 방송 듣고 계신 분들", "오늘 다룰 내용",
"내일 아침 ~ 보시거나" — 청취자를 직접 부르거나 미래 행동을 지시하는 표현은
모두 금지. 두 진행자는 서로에게만 말합니다.

### 규칙 F — 자기 검증 (매 토픽 전환 시 자문)
1. 내가 지금 도입하려는 이 사실/일화가 PRIMARY 대본에 적혀 있는가?
2. 내가 지금 쓰려는 이 비유가 PRIMARY 대본에 적혀 있는가?
3. 지금 만드는 분량이 PRIMARY 대본 길이에 비례하는가?
한 가지라도 NO 면 그 문장을 빼세요.

---

## 사실 계약 — 모든 규정에 우선하는 절대 원칙
이 에피소드에 등장할 인물·사건·숫자·발언·일시·지명은 **전적으로 PRIMARY 대본 안에 있는 것 뿐입니다**. 대본 바깥의 지식·일반 상식·추측·확장·창작을 일절 끌어들이지 마세요.

**무엇이 금지인가:**
- 대본에 없는 사건·인물·정책·통계를 **새로 도입하는 것** — 금지.
- 내용을 늘리기 위해 **배경·맥락·해설을 지어내는 것** — 방송 사고급 금지.
- 어떤 토픽을 더 두껍게 다루고 싶어도 PRIMARY 에 재료가 없으면 **짧게 끝내고 다음으로** 넘어가세요. 분량 채우려 만들어내지 마세요.
- 소스에 없는 것을 말하려는 유혹이 생기면 그냥 **아예 말하지 않고 다음 토픽** 으로 넘어가세요.
- REF 소스는 PRIMARY 의 사실을 **보강**하는 용도일 뿐입니다. **REF 에만 있고 PRIMARY 에 없는 새 사실을 도입하는 것도 금지**입니다. REF 는 PRIMARY 가 이미 다루는 토픽의 숫자·일시·인용을 더 정확히 뒷받침할 때만 쓰세요.

**실제 2026-04-19 실측에서 이 계약이 지켜지지 않아 발생한 사고 — 같은 실수를 반복하지 마세요:**
- 원본·대본 어디에도 없는 **"알리 하메네이 사망"** 서술 → 완전한 창작 (인명 오염은 방송 정정 사안)
- **"공영주차장 5부제", "미국의 아프리카 이민자 거래", "K5 권총 노후 문제"** 등 대본에 없는 무관 소재 삽입
- **"법적 제한 완화"를 "사면 논의" 로 의미 변형** — 원문 뜻을 바꾸는 것은 단순 hallucination 보다 더 위험

**자기 검증 질문 (오디오 생성 중 계속 되물어야 합니다):**
- 지금 말하려는 이 문장의 인물·사건·숫자가 PRIMARY 대본 어디에 적혀 있는가?
- 찾을 수 없다면 — 말하지 마세요.

## 프로그램 정체성
Briefly는 한국 직장인을 위한 약 8~10분 분량의 데일리 **통합 하드뉴스 브리핑**입니다. 하루 두 번(오전/오후) 제공되며, 이번 에피소드는 **{time_slot} 브리핑**입니다. 매 회차는 **정치 · 경제 · 국제** 3개 분야를 이 순서대로 하나의 에피소드에 담습니다. 분야별 개별 팟캐스트가 아니라, 세 분야를 엮은 단일 통합 브리핑입니다. KBS 라디오 뉴스나 NPR Morning Edition 같은 **정통 방송 뉴스** 톤을 따릅니다. 캐주얼한 교양·설명 팟캐스트 스타일이 아닙니다.

## 진행자와 어조
- **앵커**: 차분하고 신뢰감 있는 뉴스 앵커. 헤드라인을 전달하고 대화를 이끕니다.
- **해설**: 전문 해설위원. 배경과 맥락, 의미를 짚어줍니다.
- 두 사람 모두 **방송 뉴스 존댓말**을 씁니다: "~로 집계됐습니다", "~라고 밝혔습니다", "그렇습니다", "맞습니다".

## 금지 표현 — 이것이 가장 중요합니다
아래 표현이 나오면 이 오디오는 실패입니다. 절대 사용하지 마세요:

- **친구 수다체**: "~잖아요", "~이더라고요", "어떻게 생각하세요?", "그쵸?"
- **감탄 리액션**: "와", "오", "아", "진짜요?", "대박이네요", "신기하네요", "깜짝 놀랐어요", "헉, 세상에"
- **개인 감상**: "제가 보기엔", "정말 충격적입니다", "흥미로운 건", "재미있는 건"
- **청취자 2인칭 호명**: "여러분", "청취자님", "당신", "오늘 우리가 볼 건", "같이 살펴보시죠"
  - 청취자를 직접 부르지 말고, 3인칭 사실 서술로 전달하세요.
- **기계적 전환**: "다음 소식은", "이어서", "다음으로 넘어가서"
- **메타 언어**: "기사에 따르면", "이 자료에 보면", "제공된 내용에서는"
- **상상·도발 유도**: "상상해 보시죠", "~라고 한다면 믿으시겠어요?", "도대체 ~ 합니까?"
  - 뉴스 오프닝과 클로징은 이 instructions 뒤쪽 `구조` 섹션에 규정된 형식 한 줄만 사용.
- **심층탐구/Deep-Dive 포맷 용어**: "심층탐구", "심층탐구 미션", "파헤쳐보자", "추적해보자",
  "렌즈를 당겨보겠습니다", "이 연쇄 반응을 꿰뚫는", "이 렌즈를 그대로 우리 안방으로"
  - 이 프로그램은 뉴스 브리핑 포맷입니다. "탐구" 형식으로 변질되면 실패.

대신 정통 뉴스 어조를 사용하세요: "정부 발표에 따르면", "업계 집계에 따르면", "보도에 따르면", "매체마다 추산이 다른데".

## 구조 (약 8~10분)
1. 에피소드 전체에 **오프닝은 딱 한 번**, 맨 앞에서만 나옵니다. 앵커가 **다음 오프닝 문구를 그대로** 읽습니다 (단어·어순·문장부호 변경 금지, 다른 인사말 추가 금지):

   **{opening_line}**

2. 이어서 **정치 → 경제 → 국제** 순서로 세 분야 섹션을 진행합니다. 각 분야에 약 2~3분씩 비슷하게 배분하세요. 전체 에피소드의 총 분량은 반드시 **8~10분 범위** 안이어야 합니다 — 이 범위를 넘으면 내용이 아니라 편집 실패로 간주합니다.
3. 각 분야 내 토픽들은 제공된 순서대로 **모두** 다룹니다. 흥미로운 한두 개에만 시간을 쓰지 마세요.
4. **분야 내 토픽 전환**은 앞 토픽의 각도를 이어받는 **유기적 브릿지**로 합니다. 예: "이런 소비 흐름은 정책 쪽에도 영향을 줍니다" → 같은 분야 다음 토픽.
5. **분야 간 전환**(정치→경제, 경제→국제)은 기계적인 꼬리표를 붙이지 않습니다. 앞 분야의 맥락을 다음 분야로 자연스럽게 넘기는 의미 브릿지가 가장 좋습니다. 예: "이 정책이 시장에 줄 파장도 있는데요, 경제 쪽으로 가보죠." 가벼운 피벗("다른 분야도 짚어보죠, 경제입니다")도 허용되지만, "이제 경제 소식입니다" / "경제 소식 여기까지입니다" 같은 진행자 안내 멘트는 금지합니다.
6. 분야별 미니 오프닝·미니 클로징은 넣지 않습니다. 오프닝과 클로징은 **에피소드 전체에 각 한 번**만 존재합니다.
7. 에피소드는 앵커가 **다음 클로징 문구를 그대로** 읽고 끝맺습니다 (단어·어순·문장부호 변경 금지, 다른 마무리 인사 추가 금지):

   **{closing_line}**

   클로징 이후에는 **어떤 멘트도 덧붙이지 마세요** — 마지막 문장이 끝나는 순간 에피소드가 종료됩니다.

## 사실과 숫자
- 제공된 소스에 있는 내용만 말합니다. **외부 지식이나 일반 상식을 절대 추가하지 마세요.** 소스에 없는 숫자·날짜·인용구·사건을 만들지 마세요. 이것은 방송 뉴스의 가장 기본 원칙입니다.
- 한 문장에 들어가는 숫자는 **최대 2개**입니다. 예산 분야별 배분처럼 수치가 여러 개인 경우 문장을 나누어 읽어주세요.
  - ❌ "고유가 10조4천억, 민생 2조8천억, 산업 3조, 지방 9조7천억, 국채 1조입니다."
  - ✅ "가장 큰 몫은 고유가 부담 완화에 들어간 10조4천억 원입니다. 그다음이 지방 재정 보강으로 9조7천억 원이 배정됐습니다..."
- 숫자를 말할 때는 반드시 시점·대상 같은 맥락을 동반합니다: "매출은 190% 늘었습니다" ❌ → "지난해 하이볼 매출은 190% 늘었습니다" ✅

### 단위 보존 — 방송 사고를 막는 절대 원칙
한국어 큰 단위(**만 / 억 / 조**)를 **절대 생략하거나 줄이지 마세요**. 단위 하나를 빠뜨리면 숫자가 10,000배 왜곡됩니다. 이것은 방송 정정 사안입니다.

실제로 발생했던 치명적 오류 (같은 실수를 반복하지 마세요):
- ❌ "3,256만 명" 을 "3,256명" 으로 읽음 → **단위 탈락, 인원이 10,000배 축소**
- ❌ "1만 40톤" 을 "1만 4톤" 으로 읽음 → **자릿수 탈락, 양이 10배 축소**
- ❌ "5억 9,701만 원" 을 "5억 9,710만 원" 으로 읽음 → **마지막 두 자릿수 뒤바뀜**
- ❌ **"50조"를 "5조"로 읽음** (2026-04-20 실측) → **십의 자릿수 탈락, 매출이 10배 축소**

**2~3자리 숫자 + 단위 조합을 읽을 때 앞자릿수를 절대 생략하지 마세요**:
- "50조" → **"오십조"** (X "오조")
- "70억" → **"칠십억"** (X "칠억")
- "100만" → **"백만"** (X "만")
- "800조" → **"팔백조"** (X "팔조")

십·백·천 단위가 앞에 붙은 숫자는 그 단위까지 또박또박 발음하세요. 앞자릿수를 뭉개면 회사 매출이 1/10 로 축소되는 것과 같은 방송 정정 사안입니다.

큰 숫자를 발음할 때는 **조 · 억 · 만** 경계에서 의식적으로 짧게 쉬고, 각 단위를 또박또박 말합니다:
- "3,256만 명" → "삼천이백오십육 · 만 · 명"
- "26조 2,000억 원" → "이십육조 · 이천억 · 원"
- "5억 9,701만 원" → "오억 · 구천칠백일만 · 원"

숫자가 여러 단위에 걸쳐 있을 때 단위를 하나라도 건너뛰거나 대충 뭉개면, 그건 **뉴스 사실관계 오류**입니다. 원문에 있는 단위는 전부 살려서 발음하세요.

## 커버리지
제공된 **모든 토픽**을 빠짐없이 다룹니다. 각 토픽은 **약 40~50초 내외**로 균형 있게 배분하세요 (3분야 × 3토픽 = 9개 토픽을 8~10분 안에 담으려면 이 수준이 기준). 흥미로운 한두 가지에만 시간을 쓰는 것은 금지입니다. 반대로 목표 분량을 채우기 위해 **소스에 없는 배경 설명이나 추측을 끼워 넣는 것은 더 큰 실패** 입니다 — 주어진 사실만으로 40~50초가 나오지 않으면 그냥 짧게 끝내세요.

## 중립성 — 평가·해석·냉소 금지
정치·정책 주제에서는 찬반 입장을 동일 비중으로 다룹니다. 소스에 한쪽 관점만 있으면 그 사실만 전달하고, 반대 입장을 상상해서 만들지 마세요.

**금지되는 어휘 카테고리** (실측 실패 사례에서 추출):

- **평가 형용사**: "놀라운", "충격적", "혁신적", "파격적", "완전히 실패한", "코미디 같은", "박살이", "먹통이 된", "거창한", "아주 공격적인", "철저한", "아주 상징적인"
- **냉소·판단 관용구**: "짜고 치는 고스톱", "표 계산", "꼭 먹고 알먹고", "인신매매에 가깝다", "속에서부터 썩어들어간다", "가장 슬프고도 상징적인"
- **해석 프레임어**: "~에 가깝다", "~이나 다름없다", "사실상 ~", "~를 무시하는", "~를 외면한", "~의 진짜 출발점"
  - 원본 기사에 그 평가가 **인용**으로 명시돼 있을 때만 동일 어휘를 쓰되, 발화자 귀속(`A 의원은 ~라고 주장했습니다`) 을 함께 달아야 합니다.
- **동기·속내 해석**: 정치인·기관의 "진짜 이유" 나 "속내" 를 추측해서 서술하지 마세요. 발표·발언·행동만 전달합니다. 원본이 명시하지 않은 의도 추측 금지.

❌ 나쁜 예 (원본에 없는 해석을 저자가 부여):
  - "선거를 앞두고 표를 의식해야 하는 지자체장들 입장에서..."
  - "이 대통령 입장에선 중도·보수로 외연을 확장하려는 포석이고요"
  - "자본은 이 혼란 속에서 가장 냉철하게 자기 방어를 하고 있는 겁니다"

✅ 좋은 예 (사실·인용·수치만):
  - "공영주차장 5부제는 전국 주차장의 5%만 시행됐고, 지자체 절반은 시작하지 않았습니다."
  - "이 대통령과 홍 전 시장의 오찬에서 TK 신공항 지원과 이명박 전 대통령 관련 논의가 있었다고 보도됐습니다."

## 은유·비유 금지
뉴스 사실을 전달할 때 **은유·비유를 사용하지 마세요**. 사건·인물·숫자·정책을 **음식·게임·이동수단·스포츠·군대·자연현상·영화** 같은 다른 영역 개념에 빗대는 방식은 금지입니다.

**실측(2026-04-19~04-27)에서 발견된 금지 비유 — 같은 비유 재발생 시 실패**:
- ❌ "도시락통처럼 분리돼 있다 / 현실은 뒤엉킨 스파게티 한 그릇"
- ❌ "피자 8조각 중 두 조각을 쓰레기통에 버리면" (자사주 소각 설명)
- ❌ "벙커 3개 — 현금·의대·로또" (생존 전략 분류)
- ❌ "바다의 닌자" (스텔스 호위함)
- ❌ "핸들을 놓고 싸우는 조종사" (이란 정세 묘사)
- ❌ "산도미처럼 쌓인 외신·경제지표·정치기사"
- ❌ "정신이 팔린 블랙홀"
- ❌ **"치밀하게 돌아가는 톱니바퀴"** / **"맞물려 돌아가는 톱니"** / **"기계처럼 정교하게 작동하는"** — 정치·경제·국제 사건들을 **기계·시스템 은유**로 묶지 마세요. 사건은 사건일 뿐, 정교한 기계가 아닙니다.

**대신 직접 서술**:
- ✅ "자사주 소각은 유통 주식 수를 줄여 남은 주주의 지분 가치를 높이는 효과가 있습니다"
- ✅ "이란 외무부와 혁명수비대가 서로 다른 메시지를 내고 있습니다"
- ✅ "스텔스 호위함 11척을 호주에 수출한다고 발표했습니다"

**비유로 분량을 채우지 마세요.** 비유를 덧붙여 설명을 늘리는 것보다 사실 한 문장으로 간결하게 전달하는 쪽이 항상 더 좋습니다.

## 토픽 독립 원칙 — 메타 서사 금지
각 토픽은 **독립된 뉴스 아이템**입니다. 여러 토픽을 하나의 거대한 서사·주제·키워드로 엮지 마세요.

**금지되는 서술 방식** (실측에서 발견):
- ❌ 모든 토픽을 관통하는 키워드 설정: `"오늘의 핵심 키워드는 '생존을 위한 거래'입니다"`
- ❌ 먼 인과 연결 (비약): `"호르무즈 총알 한 발 → 지구 반대편 지자체장의 선거 공포 → 당신의 주차장"`
- ❌ 토픽 간 비유 브릿지: `"저 멀리서 누군가 면발 하나를 당겼더니..."`
- ❌ 에피소드 말미에 "모든 것이 연결돼 있다" 식 종합 메시지: `"이 모든 현상은 파편화된 뉴스가 아니라 하나의 완벽하고 거대한 서사입니다"`
- ❌ "파편화/연결됨" 프레임의 모든 변형 (실측 2026-04-27, 반복 발생):
  - `"파편화된 사건들만 쫓아간다"`
  - `"흩어진 뉴스를 자세히 보면 치밀하게 돌아가는 톱니바퀴 같은 것이 있다"`
  - `"무관해 보이는 사건들이 사실은 하나로 연결돼 있다"`
  - `"이 파편들이 어떻게 ~로 연결되는지"`
  - `"보이지 않는 흐름 / 큰 그림 / 거대한 서사"` 류
  - **이 프로그램은 "흩어진 뉴스를 꿰뚫는 통찰" 을 제공하는 자리가 아닙니다.** 청취자에게 "사실은 다 연결돼 있어요" 라고 말하지 마세요. 정치·경제·국제는 그냥 **세 개의 분리된 분야**입니다. 연결고리를 발견했다고 주장하는 순간 메타 서사이고, 곧 사실 왜곡으로 이어집니다.
- ❌ 청취자에게 도발적 질문 던지기: `"당신만의 진짜 플랜 B 는 무엇입니까?"`

**원칙**:
- **원본 기사가 명시적으로 A→B 인과를 말한 경우에만** 그 인과를 전달합니다. 그 외는 독립 보도.
- 토픽 간 전환은 **한 문장 이내의 의미 브릿지** 로만: `"이어서 경제입니다."` 수준. 비유·서사 연결 금지.
- 청취자가 여러 토픽의 의미를 연결하는 것은 **청취자의 몫**입니다. 진행자가 해석·프레임을 조립해주지 마세요.
- 이 프로그램의 역할은 "세상을 꿰뚫는 프레임 제공" 이 아니라 **깨끗한 사실 전달**입니다.

## 용어
전문 용어(추경, NPU, GPU, MoU 등)가 처음 나오면 해설이 한 문장으로 간단히 풀어 설명합니다.

## 소스 활용 원칙 — 매우 중요
이 노트북에는 두 종류의 소스가 들어 있습니다.

- **[PRIMARY]** 로 시작하는 소스 1개 = Briefly 편집팀이 작성한 통합 브리핑 **대본**. 이번 에피소드의 **진행 기준**입니다. 다루는 토픽, 토픽 순서, 카테고리 배분, 사실 전달 방식, 화자 어조까지 이 대본을 기준으로 따르세요.
- **[REF]** 로 시작하는 소스 여러 개 = 대본에서 참조한 **원본 뉴스 기사들**. 카테고리 태그(`[REF][정치]` 등)로 구분되어 있습니다.

**따를 규칙**:
1. **새 토픽 도입 금지**. REF 기사에만 있고 PRIMARY 대본에 없는 사건·인물·정책을 새로 꺼내지 마세요. 에피소드에 포함할 토픽은 PRIMARY 가 정한 것뿐입니다.
2. REF 의 역할은 **PRIMARY 가 이미 다루는 토픽의 배경·맥락·디테일을 보강**하는 것 뿐입니다. 예: PRIMARY 에 "결선 투표가 진행된다" 만 있으면, 해당 토픽의 REF 에서 결선 투표 일정·방식 같은 맥락을 가져와 해설이 한두 문장 덧붙일 수 있습니다.
3. PRIMARY 의 사실(숫자·날짜·인용)과 REF 의 사실이 **충돌**하면 PRIMARY 를 따르세요. REF 는 보조 참고 자료이고, 대본 단계에서 이미 다매체 교차 검증을 거쳤습니다.
4. 오프닝·클로징·분야 전환 브릿지는 전적으로 **PRIMARY** 를 따릅니다. REF 때문에 에피소드 구조를 바꾸지 마세요.
5. REF 기사를 직접 "인용"하지 마세요. 예: "○○일보에 따르면" 대신 PRIMARY 가 쓰는 "보도에 따르면" / "업계 집계에 따르면" 형태의 중립적 귀속을 유지합니다. (PRIMARY 에 특정 매체명이 명시된 경우에만 그대로 따릅니다.)
"""


# 오프닝·클로징 멘트 — 시간대별로 분기.
# 사용자 결정 (2026-04-27): 맨 앞에 날짜 명시 + 오후에는 "오늘 하루도 수고" 인사.
# NotebookLM 이 즉흥 창작하지 않도록 instructions 와 대본 양쪽에 동일 문구를 박아넣습니다.
# 두 문구는 script_service.py 의 EPISODE-LEVEL STRUCTURE 와 1:1 일치해야 합니다.
OPENING_LINES = {
    "오전": "안녕하세요, {date_kr} 오전입니다. Briefly 오전 브리핑, 오늘의 주요 소식 정리해드립니다.",
    "오후": "안녕하세요, {date_kr} 오후입니다. 오늘 하루도 수고 많으셨습니다. Briefly 오후 브리핑, 오늘의 주요 소식 정리해드립니다.",
}
CLOSING_LINES = {
    "오전": "지금까지 Briefly 오전 브리핑이었습니다. 활기찬 하루 보내시기 바랍니다.",
    "오후": "지금까지 Briefly 오후 브리핑이었습니다. 함께해주셔서 감사합니다. 편안한 저녁 보내시기 바랍니다.",
}


def _resolve_opening_closing(
    time_slot: str,
    briefing_date: Optional[str] = None,
) -> tuple[str, str]:
    """time_slot/날짜로부터 오프닝·클로징 문구를 만들어 반환.

    Args:
        time_slot: "오전" 또는 "오후"
        briefing_date: "YYYY-MM-DD" 문자열. None 이면 오늘(KST).

    Returns:
        (opening_line, closing_line) — 둘 다 그대로 낭독될 최종 문구.
    """
    from app.utils.date import format_briefing_date_kr

    if time_slot not in OPENING_LINES:
        raise ValueError(f"Unknown time_slot: {time_slot!r}. '오전' 또는 '오후' 만 허용.")

    date_kr = format_briefing_date_kr(briefing_date)
    opening = OPENING_LINES[time_slot].format(date_kr=date_kr)
    closing = CLOSING_LINES[time_slot]
    return opening, closing


def _build_instructions(
    time_slot: Optional[str] = None,
    version: str = "v2",
    briefing_date: Optional[str] = None,
) -> str:
    """NotebookLM 오디오 instructions를 빌드합니다.

    Args:
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 시각 기준 자동 판정.
        version: 현재 "v2"(통합 브리핑, 정통 방송 뉴스 톤)만 지원.
        briefing_date: "YYYY-MM-DD" 문자열. None 이면 오늘(KST). 오프닝 멘트 안에 들어갑니다.

    Returns:
        time_slot·오프닝·클로징이 치환된 instructions 문자열
    """
    if version != "v2":
        raise ValueError(
            f"Unsupported instructions version: {version!r}. "
            "통합 브리핑 리워크 이후 v2 만 지원합니다."
        )

    if time_slot is None:
        from app.utils.date import get_briefing_slot
        time_slot = get_briefing_slot()

    opening_line, closing_line = _resolve_opening_closing(time_slot, briefing_date)

    return INSTRUCTIONS_V2_TEMPLATE.format(
        time_slot=time_slot,
        opening_line=opening_line,
        closing_line=closing_line,
    )


async def _generate_podcast_async(
    sources: List[Dict[str, str]],
    language: str = "ko",
    method_label: str = "",
    instructions_version: str = "v2",
    time_slot: Optional[str] = None,
    briefing_date: Optional[str] = None,
) -> Optional[str]:
    """
    NotebookLM으로 통합 브리핑 팟캐스트를 생성합니다 (async 내부).

    Args:
        sources: 소스 리스트 [{"title": ..., "content": ...}, ...]. 통합 브리핑은
                 [PRIMARY] 대본 1건 + [REF] 대표 기사 27건(3분야×3토픽×3기사) 전달.
        language: 오디오 언어 코드
        method_label: 파일명에 붙일 방식 라벨 (A/B/C)
        instructions_version: 오디오 instructions 버전 (v2 만 지원)
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 기준 자동 판정.

    Returns:
        생성된 오디오 파일 경로 (str), 실패 시 None
    """
    from notebooklm import NotebookLMClient, AudioLength, DEFAULT_STORAGE_PATH

    storage = Path(DEFAULT_STORAGE_PATH)
    if not storage.exists():
        logger.error(
            f"❌ NotebookLM 인증 파일 없음: {storage}. "
            "'notebooklm login' 실행 필요."
        )
        return None

    if time_slot is None:
        from app.utils.date import get_briefing_slot
        time_slot = get_briefing_slot()

    instructions = _build_instructions(
        time_slot=time_slot,
        version=instructions_version,
        briefing_date=briefing_date,
    )
    logger.info(
        f"📋 Instructions {instructions_version} 사용 "
        f"({len(instructions)}자, time_slot={time_slot}, "
        f"briefing_date={briefing_date or 'today(KST)'})"
    )

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{method_label}" if method_label else ""
    nb_title = f"Briefly {time_slot} 통합 브리핑{label} {ts}"

    t0 = time.time()

    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(nb_title)
        logger.info(f"📓 Notebook 생성: {nb.id} ({method_label or 'default'})")

        source_ids = []
        try:
            for source in sources:
                src = await client.sources.add_text(
                    nb.id,
                    source["title"],
                    source["content"],
                    wait=False,
                )
                source_ids.append(src.id)

            logger.info(f"⏳ 소스 인덱싱 대기 ({len(source_ids)}개)...")
            await client.sources.wait_for_sources(
                nb.id, source_ids, timeout=180.0
            )

            # audio_length=SHORT 는 NotebookLM 기준 ~5-6분 hard cap.
            # 2026-04-21 실측 경로:
            #   - α+A 만 있을 때 DEFAULT → 22분 42초 (creative padding, hallucinate)
            #   - β 추가 + SHORT → 5~6분 (대본 길이와 무관하게 SHORT 가 상한)
            #   - β 추가 + DEFAULT → 12분 19초 (Pro 계정, 너무 길다는 사용자 피드백)
            # 2026-04-27 결정: 사용자가 "너무 길다" 피드백 → SHORT 로 다시 전환.
            # instructions 의 "약 8~10분" 표기는 그대로 두지만 SHORT 가 hard cap 으로 작동.
            #
            # 2026-04-21 발견된 notebooklm-py 버그 우회:
            # CREATE_ARTIFACT RPC 가 서버에서 거절되면(rate-limit/quota/장애) 라이브러리가
            # 에러를 ERROR 로그로만 찍고 status 객체를 여전히 반환. 이후 wait_for_completion
            # 이 존재하지 않는 task 를 30분 폴링하며 헛 대기. 이를 막기 위해 일시적으로
            # 로그 핸들러를 붙여 해당 에러 로그를 감지하면 즉시 RuntimeError 로 중단.

            class _CreateArtifactErrorSniffer(logging.Handler):
                """CREATE_ARTIFACT RPC 실패 로그를 감지."""
                def __init__(self):
                    super().__init__(level=logging.ERROR)
                    self.failed = False
                    self.detail = ""
                def emit(self, record):
                    try:
                        msg = record.getMessage()
                        if "CREATE_ARTIFACT" in msg and "failed" in msg:
                            self.failed = True
                            self.detail = msg
                    except Exception:
                        pass

            sniffer = _CreateArtifactErrorSniffer()
            root_logger = logging.getLogger()
            root_logger.addHandler(sniffer)
            try:
                logger.info(
                    f"🎧 오디오 생성 요청 (language={language}, length=SHORT)..."
                )
                status = await client.artifacts.generate_audio(
                    nb.id,
                    source_ids=source_ids,
                    language=language,
                    instructions=instructions,
                    audio_length=AudioLength.SHORT,
                )
                # ERROR 로그가 flush 될 시간 (라이브러리 내부 async 처리 여유)
                await asyncio.sleep(0.5)
                if sniffer.failed:
                    raise RuntimeError(
                        f"NotebookLM CREATE_ARTIFACT RPC 거절됨 — {sniffer.detail}. "
                        "서버 rate-limit / quota / 장애 의심. 30분 헛 대기 방지를 위해 즉시 중단."
                    )
            finally:
                root_logger.removeHandler(sniffer)

            # 2026-04-20 실측: 대본 7,220자 + REF 37건 구성에서 SHORT 이어도 NotebookLM
            # 생성 시간이 20분을 초과해 timeout. 서버 부하·대본 길이 증가에 여유 두고
            # 30분으로 상향. 정상 케이스는 여전히 10~15분 안에 완료됨.
            logger.info(f"⏳ 생성 완료 대기 (최대 30분)...")
            await client.artifacts.wait_for_completion(
                nb.id, status.task_id, timeout=1800.0
            )

            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            output_path = str(
                output_dir / f"podcast_{time_slot}{label}_{ts}.mp3"
            )

            await client.artifacts.download_audio(nb.id, output_path)
            elapsed = time.time() - t0

            logger.info(
                f"✅ 팟캐스트 생성 완료: {output_path} ({elapsed:.1f}초)"
            )
            return output_path

        except Exception as e:
            logger.error(
                f"❌ 팟캐스트 생성 실패: {type(e).__name__}: {e}",
                exc_info=True,
            )
            resp = getattr(e, "response", None)
            if resp is not None:
                logger.error(
                    f"  Response status: {getattr(resp, 'status_code', '?')}"
                )
                body = getattr(resp, "text", None) or getattr(resp, "content", None)
                if body:
                    logger.error(f"  Response body: {str(body)[:1000]}")
            return None

        finally:
            try:
                await client.notebooks.delete(nb.id)
                logger.info("🗑️ Notebook 정리 완료")
            except Exception:
                pass


def _build_podcast_sources(
    script: str,
    time_slot: str,
    reference_articles: Optional[List[Dict]] = None,
) -> List[Dict[str, str]]:
    """통합 브리핑 대본(PRIMARY) + 대표 원본 기사들(REF)을 NotebookLM 소스 리스트로 변환.

    설계 의도 — 대본만 단일 소스로 보내면 NotebookLM 이 DEFAULT(10~15분) 길이를
    채우기 위해 대본에 없는 내용을 지어내거나 반복할 위험이 있습니다. 하드뉴스
    3분야 × top 3 클러스터 × 대표 기사 3건 = 총 **27건** 원본 기사를 REF 소스로
    같이 넣어 NotebookLM 이 확장 시 끌어올 "팩트 저수지"로 쓰게 합니다.

    제목 접두어 [PRIMARY] / [REF] 는 INSTRUCTIONS_V2_TEMPLATE '## 소스 활용 원칙'
    섹션과 짝을 이뤄 NotebookLM 에 소스 위계를 전달합니다.

    대본은 NotebookLM TTS 의 숫자 단위 탈락 오류를 막기 위해 `_tts_safe_numbers()`
    로 전처리됩니다. REF 기사 본문은 길이 상한 3000자로 트리밍.
    """
    sources: List[Dict[str, str]] = [{
        "title": f"[PRIMARY] Briefly {time_slot} 통합 브리핑 대본",
        "content": _tts_safe_numbers(_strip_code_fence(script)),
    }]

    if not reference_articles:
        return sources

    for a in reference_articles:
        title = (a.get("title") or "").strip()
        content = (a.get("content") or a.get("lede") or "").strip()
        if not title or not content:
            continue
        press = (a.get("press") or a.get("provider") or "").strip()
        category_ko = (a.get("category_ko") or "").strip()

        # NotebookLM 소스 제목 표시 한도를 감안해 200자 상한
        prefix = f"[REF][{category_ko}]" if category_ko else "[REF]"
        display_title = f"{prefix} [{press}] {title}" if press else f"{prefix} {title}"
        sources.append({
            "title": display_title[:200],
            "content": content[:3000],
        })

    return sources


def generate_podcast(
    script: str,
    time_slot: Optional[str] = None,
    reference_articles: Optional[List[Dict]] = None,
    language: str = "ko",
    instructions_version: str = "v2",
    briefing_date: Optional[str] = None,
) -> Optional[str]:
    """
    GPT 대본(정치·경제·국제 통합) + 대표 원본 기사들을 NotebookLM 에 넘겨 팟캐스트
    오디오를 생성합니다.

    통합 브리핑 모델 전용. 카테고리별 개별 팟캐스트는 더 이상 지원하지 않습니다.

    Args:
        script: generate_script()로 생성된 통합 브리핑 대본 텍스트 (PRIMARY 소스).
        time_slot: "오전" 또는 "오후". None 이면 현재 KST 기준 자동 판정.
        reference_articles: NotebookLM 이 확장 시 참조할 원본 기사 리스트 (REF 소스).
            통합 브리핑 스케줄러 기준 3분야 × top 3 클러스터 × 대표 기사 3건 = 27건
            전달 권장. None 이면 REF 없이 대본 단일 소스로 생성.
        language: 오디오 언어 코드.
        instructions_version: 오디오 instructions 버전 (현재 v2 만 지원).
        briefing_date: "YYYY-MM-DD" 문자열. None 이면 오늘(KST). 오프닝 멘트의 날짜 표기에 사용.

    Returns:
        생성된 오디오 파일 경로, 실패 시 None.
    """
    if not script:
        logger.error("대본이 비어 있습니다.")
        return None

    if time_slot is None:
        from app.utils.date import get_briefing_slot
        time_slot = get_briefing_slot()

    sources = _build_podcast_sources(script, time_slot, reference_articles)
    n_refs = len(sources) - 1
    logger.info(
        f"🎙️ 통합 브리핑 → NotebookLM "
        f"(time_slot={time_slot}, PRIMARY 1건 + REF {n_refs}건 = 총 {len(sources)}개 소스)"
    )

    return asyncio.run(
        _generate_podcast_async(
            sources,
            language=language,
            method_label="podcast",
            instructions_version=instructions_version,
            time_slot=time_slot,
            briefing_date=briefing_date,
        )
    )


def check_auth() -> bool:
    """NotebookLM 인증 상태를 확인합니다."""
    from notebooklm import DEFAULT_STORAGE_PATH

    storage = Path(DEFAULT_STORAGE_PATH)
    if not storage.exists():
        return False

    # 간단한 API 호출로 쿠키 유효성 검사
    async def _check():
        from notebooklm import NotebookLMClient
        try:
            async with await NotebookLMClient.from_storage() as client:
                await client.notebooks.list()
                return True
        except Exception:
            return False

    return asyncio.run(_check())


def refresh_auth(wait_before_enter: float = 10.0) -> bool:
    """
    NotebookLM 인증을 자동 갱신합니다.

    `notebooklm login`을 실행하면 브라우저가 열리고 Google OAuth로 리다이렉트됩니다.
    브라우저에 이미 Google 로그인이 돼 있으면 자동으로 인증이 완료되고,
    CLI에서 Enter만 치면 쿠키가 저장됩니다.

    이 함수는 login 프로세스 실행 → 10초 대기(OAuth 완료 대기) → Enter 전송 →
    완료 대기 → check_auth()로 성공 여부 확인 순서로 동작합니다.

    Args:
        wait_before_enter: Enter 전송 전 대기 시간 (초). 기본 10초.

    Returns:
        갱신 성공 여부
    """
    import subprocess

    logger.info(f"🔐 NotebookLM 인증 갱신 시도 (Enter 전 {wait_before_enter}초 대기)...")

    try:
        proc = subprocess.Popen(
            ["notebooklm", "login"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 브라우저가 열리고 OAuth 리다이렉트가 완료될 때까지 대기
        time.sleep(wait_before_enter)

        # Enter 전송
        proc.stdin.write(b"\n")
        proc.stdin.flush()

        # 프로세스 완료 대기 (최대 30초)
        proc.wait(timeout=30)

        if proc.returncode != 0:
            stderr = proc.stderr.read().decode(errors="replace")
            logger.warning(f"  ⚠️ notebooklm login 비정상 종료 (code={proc.returncode}): {stderr[:200]}")

    except subprocess.TimeoutExpired:
        proc.kill()
        logger.error("  ❌ notebooklm login 타임아웃 (30초)")
        return False
    except FileNotFoundError:
        logger.error("  ❌ notebooklm CLI를 찾을 수 없습니다. pip install notebooklm 필요.")
        return False
    except Exception as e:
        logger.error(f"  ❌ 인증 갱신 실패: {e}")
        return False

    # 갱신 성공 여부 확인
    ok = check_auth()
    if ok:
        logger.info("  ✅ 인증 갱신 성공")
    else:
        logger.error("  ❌ 인증 갱신 후에도 인증 실패")
    return ok


def ensure_auth() -> bool:
    """
    인증을 확인하고, 만료됐으면 자동 갱신을 시도합니다.

    scheduler.py에서 오디오 생성 전에 호출하는 통합 인터페이스.

    Returns:
        인증 유효 여부 (갱신 시도 포함)
    """
    if check_auth():
        return True

    logger.warning("  ⚠️ NotebookLM 인증 만료 → 자동 갱신 시도")
    return refresh_auth()
