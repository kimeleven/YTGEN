"""
edge-tts로 텍스트를 MP3 음성 파일로 변환한다.
한국어/일본어/중국어 목소리 지원.
"""
import asyncio
import os
from typing import Optional

import edge_tts

# ── 언어별 기본 목소리 ────────────────────────────────────────────────────────
DEFAULT_VOICES = {
    "ko": "ko-KR-SunHiNeural",    # 한국어 여성 (밝고 발랄)
    "ja": "ja-JP-NanamiNeural",   # 일본어 여성 (자연스러운)
    "zh": "zh-CN-XiaoxiaoNeural", # 중국어 여성 (명료한)
}

DEFAULT_RATE = "+25%"  # 기본 속도 (양수: 빠름, 음수: 느림)


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
        language: 언어 코드 ("ko" | "ja" | "zh")
        voice: edge-tts 목소리 이름 (None이면 language 기준 기본값 사용)
        speed: 속도 조절 (+25%, -10% 등)
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    selected_voice = voice or DEFAULT_VOICES.get(language, DEFAULT_VOICES["ko"])
    selected_rate  = speed or DEFAULT_RATE

    asyncio.run(_async_generate(text, output_path, selected_voice, selected_rate))

    print(f"[tts_gen] 음성 생성 완료: {output_path} (목소리: {selected_voice}, 속도: {selected_rate})")
    return output_path
