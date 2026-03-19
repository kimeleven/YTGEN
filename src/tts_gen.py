"""
edge-tts로 텍스트를 MP3 음성 파일로 변환한다.
한국어 여성 목소리, 빠른 속도 지원.
"""
import asyncio
import os
from typing import Optional

import edge_tts

# ── 사용 가능한 한국어 여성 목소리 ──────────────────────────────────────────────
VOICES = {
    "sunhi":  "ko-KR-SunHiNeural",   # 밝고 발랄한 여성 (기본)
    "yujin":  "ko-KR-YuJinNeural",   # 젊고 활기찬 여성
    "hyunsu": "ko-KR-HyunsuNeural",  # 남성 (대안)
}

DEFAULT_VOICE = "ko-KR-SunHiNeural"
DEFAULT_RATE  = "+25%"   # 기본 속도 (양수: 빠름, 음수: 느림)


async def _async_generate(text: str, output_path: str, voice: str, rate: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(output_path)


def generate_tts(
    text: str,
    output_path: str,
    language: str = "ko",
    voice: Optional[str] = None,
    speed: Optional[str] = None,
) -> str:
    """
    텍스트를 TTS로 변환해 MP3 파일로 저장하고 경로를 반환한다.

    Args:
        text: 변환할 텍스트
        output_path: 저장 경로 (.mp3)
        language: 언어 코드 (현재 ko만 지원)
        voice: edge-tts 목소리 이름 (None이면 기본값 사용)
        speed: 속도 조절 (+25%, -10% 등)
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    selected_voice = voice or DEFAULT_VOICE
    selected_rate  = speed or DEFAULT_RATE

    asyncio.run(_async_generate(text, output_path, selected_voice, selected_rate))

    print(f"[tts_gen] 음성 생성 완료: {output_path} (목소리: {selected_voice}, 속도: {selected_rate})")
    return output_path


