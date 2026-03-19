"""
이미지 + 음성 + 자막을 조합해 YouTube Shorts MP4를 생성한다.
moviepy 1.0.3 기준.
"""
import os
import textwrap
from datetime import datetime
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    ImageClip,
    concatenate_videoclips,
)


# ── 자막 렌더링 ────────────────────────────────────────────────────────────────

def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """폰트 로드. 실패 시 기본 폰트 사용."""
    fallbacks = [
        font_path,
        # Windows
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        # Linux (Ubuntu: fonts-nanum)
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in fallbacks:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    print("[video_maker] 경고: 트루타입 폰트 없음, 기본 폰트 사용 (한글 깨질 수 있음)")
    return ImageFont.load_default()


def _strip_emoji(text: str) -> str:
    """이모지를 제거한다. 한글/영문/숫자는 보존."""
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 감정 이모지
        "\U0001F300-\U0001F5FF"  # 기호/픽토그램
        "\U0001F680-\U0001F6FF"  # 교통/지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U0001F900-\U0001F9FF"  # 보충 기호
        "\U0001FA00-\U0001FAFF"  # 추가 이모지
        "\U00002702-\U000027B0"  # 딩뱃
        "\U00002500-\U00002BFF"  # 박스/기하 기호
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text).strip()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw) -> list[str]:
    """텍스트를 max_width에 맞게 줄바꿈한다."""
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip() if current else word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines if lines else [text]


def _draw_subtitle(
    img: Image.Image,
    text: str,
    font_path: str,
    font_size: int,
    color: tuple,
    stroke_color: tuple,
    stroke_width: int,
    box_opacity: int,
    padding_bottom: int,
) -> Image.Image:
    """이미지 하단에 자막을 베이크인해 반환한다."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    font = _load_font(font_path, font_size)

    text = _strip_emoji(text)  # 이모지 제거
    w, h = img.size
    max_text_width = w - 80  # 좌우 40px 패딩
    lines = _wrap_text(text, font, max_text_width, draw)

    line_height = font_size + 12
    total_text_h = len(lines) * line_height + 20  # 상하 10px 내부 패딩
    box_bottom = h - padding_bottom
    box_top = box_bottom - total_text_h

    # 반투명 배경 박스
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rounded_rectangle(
        [(30, box_top - 10), (w - 30, box_bottom + 10)],
        radius=16,
        fill=(0, 0, 0, box_opacity),
    )
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 텍스트 (stroke + 본문)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        y = box_top + i * line_height

        # 8방향 stroke
        for dx in [-stroke_width, 0, stroke_width]:
            for dy in [-stroke_width, 0, stroke_width]:
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), line, font=font, fill=tuple(stroke_color))

        # 본문
        draw.text((x, y), line, font=font, fill=tuple(color))

    return img


# ── 영상 제작 ──────────────────────────────────────────────────────────────────

def make_video(
    segments: list[dict],
    output_path: str,
    subtitle_cfg: dict,
    bgm_cfg: Optional[dict] = None,
    fps: int = 30,
) -> str:
    """
    segments: [{"image": PIL.Image, "audio_path": str, "narration": str}, ...]
    subtitle_cfg: config.yaml의 subtitle 섹션
    bgm_cfg: config.yaml의 bgm 섹션 (None이면 BGM 없음)
    반환: 생성된 MP4 파일 경로
    """
    clips = []

    for i, seg in enumerate(segments):
        print(f"[video_maker] 세그먼트 {i + 1}/{len(segments)} 처리 중...")

        audio_clip = AudioFileClip(seg["audio_path"])
        duration = audio_clip.duration

        # 자막 베이크인
        frame = _draw_subtitle(
            img=seg["image"],
            text=seg["narration"],
            font_path=subtitle_cfg.get("font_path", "C:/Windows/Fonts/malgunbd.ttf"),
            font_size=subtitle_cfg.get("font_size", 55),
            color=subtitle_cfg.get("color", [255, 255, 255]),
            stroke_color=subtitle_cfg.get("stroke_color", [0, 0, 0]),
            stroke_width=subtitle_cfg.get("stroke_width", 3),
            box_opacity=subtitle_cfg.get("box_opacity", 160),
            padding_bottom=subtitle_cfg.get("padding_bottom", 120),
        )

        frame_arr = np.array(frame)
        video_clip = (
            ImageClip(frame_arr)
            .set_duration(duration)
            .set_fps(fps)
            .set_audio(audio_clip)
        )
        clips.append(video_clip)

    print("[video_maker] 클립 연결 중...")
    final = concatenate_videoclips(clips, method="compose")

    # ── BGM 믹싱 ──────────────────────────────────────────────
    if bgm_cfg and bgm_cfg.get("enabled", False):
        bgm_path = bgm_cfg.get("path", "temp/bgm.wav")
        bgm_volume = bgm_cfg.get("volume", 0.15)

        # BGM이 없으면 생성
        if not os.path.exists(bgm_path):
            from src.music_gen import generate_bgm
            os.makedirs(os.path.dirname(bgm_path), exist_ok=True)
            generate_bgm(
                duration_seconds=final.duration + 1,
                output_path=bgm_path,
                volume=1.0,   # volumex로 따로 조절
            )

        bgm_clip = (
            AudioFileClip(bgm_path)
            .set_duration(final.duration)
            .volumex(bgm_volume)
        )
        mixed_audio = CompositeAudioClip([final.audio, bgm_clip])
        final = final.set_audio(mixed_audio)
        print(f"[video_maker] BGM 믹싱 완료 (볼륨 {bgm_volume})")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    print(f"[video_maker] 영상 인코딩 중... → {output_path}")
    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp/final_audio.m4a",
        remove_temp=True,
        verbose=False,
        logger=None,
    )

    # 리소스 해제
    for c in clips:
        c.close()
    final.close()

    print(f"[video_maker] 완료: {output_path}")
    return output_path


def generate_output_filename(title: str, output_dir: str) -> str:
    """타임스탬프 기반 출력 파일명을 생성한다."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:30].strip()
    filename = f"{ts}_{safe_title}.mp4"
    return os.path.join(output_dir, filename)
