"""
numpy + wave 모듈로 앰비언트 배경음악(WAV)을 생성한다.
외부 의존성 없이 순수 Python으로 동작.
"""
import math
import os
import struct
import wave


# ── 음표 주파수 (Hz) ──────────────────────────────────────────────────────────
_CHORDS = {
    "C_major":  [261.63, 329.63, 392.00, 523.25],   # C4 E4 G4 C5
    "G_major":  [196.00, 246.94, 293.66, 392.00],   # G3 B3 D4 G4
    "Am":       [220.00, 261.63, 329.63, 440.00],   # A3 C4 E4 A4
    "F_major":  [174.61, 220.00, 261.63, 349.23],   # F3 A3 C4 F4
}

_CHORD_SEQUENCE = ["C_major", "Am", "F_major", "G_major"]


def generate_bgm(duration_seconds: float, output_path: str, volume: float = 0.15) -> str:
    """
    앰비언트 배경음악 WAV 파일을 생성한다.

    Args:
        duration_seconds: 총 길이 (초)
        output_path: 저장 경로
        volume: 볼륨 0.0~1.0 (기본 0.15)

    Returns:
        저장된 파일 경로
    """
    sample_rate = 44100
    n_samples = int(sample_rate * duration_seconds)
    chord_duration = sample_rate * 4   # 코드 하나당 4초

    samples = []
    for i in range(n_samples):
        t = i / sample_rate

        # 현재 코드 결정 (4초 단위 순환)
        chord_idx = (i // chord_duration) % len(_CHORD_SEQUENCE)
        freqs = _CHORDS[_CHORD_SEQUENCE[chord_idx]]

        # 코드 내 음표 합산
        value = 0.0
        for freq in freqs:
            # 기본 사인파 + 2배음 (약하게) → 따뜻한 패드 음색
            value += math.sin(2 * math.pi * freq * t)
            value += math.sin(2 * math.pi * freq * 2 * t) * 0.25

        # 음표 수로 정규화
        value /= len(freqs) * 1.25

        # 느린 진폭 변조 (0.1Hz 트레몰로) → 공간감
        tremolo = 0.85 + 0.15 * math.sin(2 * math.pi * 0.1 * t)
        value *= tremolo

        # 전체 볼륨 적용
        value *= volume

        # 페이드인 (2초)
        fade_in_samples = sample_rate * 2
        if i < fade_in_samples:
            value *= i / fade_in_samples

        # 페이드아웃 (2초)
        fade_out_start = n_samples - sample_rate * 2
        if i > fade_out_start:
            value *= (n_samples - i) / (sample_rate * 2)

        samples.append(value)

    # int16 변환 후 WAV 저장
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)          # 모노
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(sample_rate)
        packed = struct.pack(f"<{len(samples)}h", *[int(s * 32767) for s in samples])
        wf.writeframes(packed)

    print(f"[music_gen] BGM 생성 완료 ({duration_seconds:.1f}s) → {output_path}")
    return output_path
