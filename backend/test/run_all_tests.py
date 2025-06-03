#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test/run_all_tests.py

import os
import sys
import subprocess
import time
from datetime import datetime

# PowerShell 환경에서 UTF-8 인코딩 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_test_file(test_file):
    """개별 테스트 파일 실행"""
    print(f"🔄 {test_file} 실행중...")
    start_time = time.time()
    
    try:
        # UTF-8 인코딩 환경변수와 함께 실행
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, encoding='utf-8', cwd=os.path.dirname(__file__), env=env)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file} 완료 ({duration:.1f}초)")
            # 디버깅: 출력 길이 정보 추가
            stdout_len = len(result.stdout) if result.stdout else 0
            stderr_len = len(result.stderr) if result.stderr else 0
            if test_file == "test_collection_simulation.py":
                print(f"  🔍 stdout 길이: {stdout_len}자, stderr 길이: {stderr_len}자")
                if result.stdout:
                    print(f"  📝 출력 미리보기: {result.stdout[:100]}...")
            return True, result.stdout, ""
        else:
            print(f"❌ {test_file} 실패 ({duration:.1f}초)")
            return False, result.stdout, result.stderr
            
    except Exception as e:
        print(f"🚨 {test_file} 실행 오류: {e}")
        return False, "", str(e)

def main():
    """전체 테스트 실행"""
    print("🚀 Briefly 전체 유닛테스트 실행")
    print("=" * 50)
    print(f"📅 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 실행할 테스트 파일 목록
    test_files = [
        "test_frequency_unit.py",
        "test_collection_simulation.py", 
        "test_clustering.py",
        "test_content_extraction.py",
        "test_utils.py",
        "test_tts_service.py"
    ]
    
    # 테스트 파일 존재 확인
    existing_files = []
    missing_files = []
    
    for test_file in test_files:
        if os.path.exists(test_file):
            existing_files.append(test_file)
        else:
            missing_files.append(test_file)
    
    print(f"📊 테스트 파일 현황:")
    print(f"  - 존재: {len(existing_files)}개")
    print(f"  - 누락: {len(missing_files)}개")
    
    if missing_files:
        print(f"⚠️ 누락된 파일: {missing_files}")
    print()
    
    # 개별 테스트 실행
    results = {}
    total_start = time.time()
    
    for test_file in existing_files:
        success, stdout, stderr = run_test_file(test_file)
        results[test_file] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
        print()  # 구분선
    
    total_end = time.time()
    total_duration = total_end - total_start
    
    # 결과 요약
    print("=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {total_count - success_count}개")
    print(f"📊 성공률: {success_count/total_count*100:.1f}%")
    print(f"⏱️ 총 소요시간: {total_duration:.1f}초")
    print()
    
    # 개별 결과 상세
    print("📋 개별 테스트 결과:")
    for test_file, result in results.items():
        status = "✅" if result["success"] else "❌"
        test_name = test_file.replace("test_", "").replace(".py", "")
        print(f"  {status} {test_name}")
        
        if not result["success"] and result["stderr"]:
            print(f"    오류: {result['stderr'][:100]}...")
    
    print()
    
    # 실패한 테스트 상세 정보
    failed_tests = [name for name, result in results.items() if not result["success"]]
    if failed_tests:
        print("🚨 실패한 테스트 상세:")
        for test_file in failed_tests:
            result = results[test_file]
            print(f"\n📋 {test_file}:")
            if result["stderr"]:
                print("에러 메시지:")
                print(result["stderr"])
            if result["stdout"]:
                print("출력:")
                print(result["stdout"][-500:])  # 마지막 500자만
    
    # 테스트 범위 확인
    print("\n🎯 테스트 범위:")
    test_coverage = {
        "test_frequency_unit.py": "카테고리, 뉴스수집, 대본생성",
        "test_collection_simulation.py": "뉴스수집 로직 시뮬레이션",
        "test_clustering.py": "이중 클러스터링 전략",
        "test_content_extraction.py": "본문추출, 노이즈제거",
        "test_utils.py": "날짜, 카테고리, 환경설정",
        "test_tts_service.py": "TTS 음성변환 서비스"
    }
    
    for test_file, description in test_coverage.items():
        status = "✅" if test_file in existing_files else "❌"
        print(f"  {status} {description}")
    
    # 권장사항
    print(f"\n💡 권장사항:")
    if success_count == total_count:
        print("🎉 모든 테스트가 통과했습니다!")
        print("  - 운영환경 배포 준비 완료")
        print("  - CI/CD 파이프라인 연동 권장")
    else:
        print("⚠️ 실패한 테스트를 수정해주세요:")
        print("  - 실패 원인 분석 및 코드 수정")
        print("  - 환경변수 설정 확인")
        print("  - 외부 API 의존성 확인")
    
    print(f"\n🏁 전체 테스트 완료!")
    
    # 종료 코드 반환
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 