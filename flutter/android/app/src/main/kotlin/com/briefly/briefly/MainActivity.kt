package com.briefly.briefly

// audio_service 플러그인(just_audio_background 의 기반)이 요구하는 activity base class.
// `AudioServiceActivity` 는 `FlutterFragmentActivity` 의 서브클래스로,
// 백그라운드 오디오 세션 + 락스크린/알림 컨트롤을 자동 설정합니다.
import com.ryanheise.audioservice.AudioServiceActivity

class MainActivity : AudioServiceActivity()
