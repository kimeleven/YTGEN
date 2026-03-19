"""
Gemini Imagen 3으로 배경 이미지를 생성한다.
API 오류 시 PIL 그라디언트 배경으로 fallback.
"""
import io
import os
import random

from PIL import Image, ImageDraw


def generate_image(prompt: str, size: tuple = (1080, 1920)) -> Image.Image:
    """
    이미지 프롬프트를 받아 PIL Image를 반환한다.
    Gemini Flash Image → Imagen 4 → 그라디언트 순으로 fallback.
    """
    for fn, name in [
        (_generate_with_gemini_flash, "Gemini Flash Image"),
        (_generate_with_imagen4, "Imagen 4"),
    ]:
        try:
            return fn(prompt, size)
        except Exception as e:
            print(f"[image_gen] {name} 실패 ({e}), 다음 방법 시도...")

    print("[image_gen] 모든 이미지 생성 실패, 그라디언트 fallback 사용")
    return _gradient_fallback(size)


def _resize_cover(img: Image.Image, size: tuple) -> Image.Image:
    """target 비율(9:16)에 맞게 crop-resize (생성 이미지가 정사각형일 때 사용)."""
    tw, th = size
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def _generate_with_gemini_flash(prompt: str, size: tuple) -> Image.Image:
    """Gemini 2.5 Flash Image 모델로 이미지 생성."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 없습니다.")

    client = genai.Client(api_key=api_key)

    enhanced = (
        f"{prompt}. "
        "High quality digital art, vibrant colors, cinematic lighting, "
        "no text, no watermark, no logo."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=enhanced,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            img = Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
            img = _resize_cover(img, size)
            print("[image_gen] Gemini Flash Image 생성 완료")
            return img

    raise RuntimeError("Gemini Flash Image 응답에 이미지 데이터 없음")


def _generate_with_imagen4(prompt: str, size: tuple) -> Image.Image:
    """Imagen 4로 이미지 생성."""
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 없습니다.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="9:16",
        ),
    )

    image_bytes = response.generated_images[0].image.image_bytes
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(size, Image.LANCZOS)
    print("[image_gen] Imagen 4 생성 완료")
    return img


def _gradient_fallback(size: tuple) -> Image.Image:
    """컬러 그라디언트 배경 이미지를 생성한다."""
    color_pairs = [
        [(15, 15, 60), (80, 15, 120)],   # 블루-퍼플
        [(10, 60, 10), (10, 120, 80)],   # 그린
        [(60, 15, 15), (120, 60, 10)],   # 레드-오렌지
        [(10, 40, 80), (60, 10, 100)],   # 인디고
        [(40, 10, 60), (10, 80, 120)],   # 퍼플-틸
        [(60, 40, 10), (10, 60, 80)],    # 골든-틸
    ]

    top_c, bot_c = random.choice(color_pairs)
    w, h = size

    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)

    for y in range(h):
        t = y / h
        r = int(top_c[0] * (1 - t) + bot_c[0] * t)
        g = int(top_c[1] * (1 - t) + bot_c[1] * t)
        b = int(top_c[2] * (1 - t) + bot_c[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    print(f"[image_gen] 그라디언트 배경 생성 완료")
    return img
