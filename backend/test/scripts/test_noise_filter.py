"""
노이즈 필터 테스트 스크립트
기존 샘플 데이터(samples_3k_5k.json)에 새 필터 적용하여 결과 확인
"""
import json
import re

# 노이즈 탐지용 키워드 (메뉴/네비게이션/푸터에서 자주 발견)
NOISE_KEYWORDS = {
    '닫기', '로그인', '회원가입', '전체메뉴', '오피니언',
    '개인정보처리방침', '청소년보호정책', '인기기사', '최신기사',
    '댓글정책', '구독신청', '뉴스레터', '광고문의'
}

def is_korean_text(text: str, threshold: float = 0.7) -> bool:
    """텍스트 내 한글 비율 검사"""
    kor_count = len(re.findall(r"[가-힣]", text))
    total_count = len(re.findall(r"[가-힣a-zA-Z]", text))
    if total_count == 0:
        return False
    return kor_count / total_count >= threshold

def is_structural_noise(content: str) -> bool:
    """구조적 메트릭 기반 노이즈 탐지"""
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) < 5:
        return False

    short_lines = sum(1 for l in lines if len(l) < 10)
    short_ratio = short_lines / len(lines)
    avg_line_len = len(content) / len(lines)

    if short_ratio > 0.30 and avg_line_len < 20:
        return True
    return False

def count_noise_keywords(content: str) -> int:
    """노이즈 키워드 출현 횟수 반환"""
    count = 0
    for kw in NOISE_KEYWORDS:
        count += content.count(kw)
    return count

def analyze_article(content: str) -> dict:
    """기사 분석"""
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    short_lines = sum(1 for l in lines if len(l) < 10)

    return {
        "length": len(content),
        "total_lines": len(lines),
        "short_lines": short_lines,
        "short_ratio": round(short_lines / len(lines) * 100, 1) if lines else 0,
        "avg_line_len": round(len(content) / len(lines), 1) if lines else 0,
        "noise_keywords": count_noise_keywords(content),
        "is_structural_noise": is_structural_noise(content),
        "is_korean": is_korean_text(content, 0.7)
    }

def main():
    # 샘플 로드
    with open('d:\\Github\\Briefly\\backend\\test\\results\\samples_3k_5k.json', 'r', encoding='utf-8') as f:
        samples = json.load(f)

    # 이전 분석 결과 (정답) 로드
    with open('d:\\Github\\Briefly\\backend\\test\\results\\quality_analysis_3k_5k.json', 'r', encoding='utf-8') as f:
        expected = json.load(f)

    expected_verdicts = {item["index"]: item["verdict"] for item in expected}

    print("=" * 80)
    print("노이즈 필터 테스트 결과")
    print("=" * 80)

    results = []
    correct = 0

    for i, sample in enumerate(samples, 1):
        content = sample.get("content", "")
        analysis = analyze_article(content)

        # 새 필터 적용 결과
        if analysis["is_structural_noise"]:
            new_verdict = "NOISE (structural)"
        elif analysis["noise_keywords"] >= 3:
            new_verdict = "NOISE (keywords)"
        else:
            new_verdict = "OK"

        # 정답 비교
        expected_verdict = expected_verdicts.get(i, "?")
        is_correct = (new_verdict.startswith("OK") == (expected_verdict == "OK"))
        if is_correct:
            correct += 1

        result = {
            "index": i,
            "provider": sample.get("provider", "?"),
            "title": sample.get("title", "?")[:40],
            "expected": expected_verdict,
            "new_verdict": new_verdict,
            "correct": is_correct,
            **analysis
        }
        results.append(result)

        match_str = "O" if is_correct else "X"
        print(f"\n[{i}] {sample.get('provider', '?')} - {sample.get('title', '?')[:30]}...")
        print(f"    길이: {analysis['length']}, 줄수: {analysis['total_lines']}, 짧은줄: {analysis['short_ratio']}%")
        print(f"    평균줄길이: {analysis['avg_line_len']}, 노이즈키워드: {analysis['noise_keywords']}")
        print(f"    구조적노이즈: {analysis['is_structural_noise']}")
        print(f"    예상: {expected_verdict} -> 새필터: {new_verdict} [{match_str}]")

    print("\n" + "=" * 80)
    print(f"정확도: {correct}/{len(samples)} ({correct/len(samples)*100:.1f}%)")
    print("=" * 80)

    # 결과 저장
    with open('d:\\Github\\Briefly\\backend\\test\\results\\noise_filter_test.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n결과 저장: test/results/noise_filter_test.json")

if __name__ == "__main__":
    main()
