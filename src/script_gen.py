"""
Gemini API를 사용해 YouTube Shorts 대본을 JSON 형태로 생성한다.
일반 주제 또는 뉴스 기사 기반 대본 모두 지원.
언어(ko/ja/zh)를 지정해 해당 언어 대본을 생성할 수 있다.
"""
import json
import os
import re

from google import genai


# 언어별 프롬프트 설정
_LANG_CONFIG = {
    "ko": {
        "instruction": "한국어 YouTube Shorts 대본을 작성해주세요.",
        "narration_hint": "나레이션 텍스트 (한국어, 50~80자, 이모지 없음, 사실 중심)",
        "title_hint": "영상 제목 (40자 이내, 핵심 내용 포함, 이모지 없음)",
        "desc_hint": "영상 설명 (100자 이내, 핵심 내용 요약, 해시태그 포함)",
        "tags_hint": '["AI", "인공지능", "태그3", "태그4", "태그5"]',
        "closing": "구독과 알림 설정으로 AI 뉴스를 가장 빠르게 받아보세요.",
        "char_rule": "한글, 숫자, 마침표, 쉼표만 사용 (이모지·특수문자 절대 금지)",
    },
    "ja": {
        "instruction": "日本語でYouTube Shortsの台本を作成してください。",
        "narration_hint": "ナレーションテキスト（日本語、50〜80文字、絵文字なし、事実中心）",
        "title_hint": "動画タイトル（40文字以内、核心内容含む、絵文字なし）",
        "desc_hint": "動画説明（100文字以内、核心内容要約、ハッシュタグ含む）",
        "tags_hint": '["AI", "人工知能", "タグ3", "タグ4", "タグ5"]',
        "closing": "チャンネル登録と通知をオンにして最新AIニュースをお届けします。",
        "char_rule": "日本語（ひらがな・カタカナ・漢字）、数字、句読点のみ使用（絵文字・特殊文字禁止）",
    },
    "zh": {
        "instruction": "请用中文撰写YouTube Shorts脚本。",
        "narration_hint": "旁白文字（中文，50~80字，无表情符号，以事实为中心）",
        "title_hint": "视频标题（40字以内，包含核心内容，无表情符号）",
        "desc_hint": "视频说明（100字以内，核心内容摘要，包含话题标签）",
        "tags_hint": '["AI", "人工智能", "标签3", "标签4", "标签5"]',
        "closing": "订阅频道并开启通知，第一时间获取最新AI资讯。",
        "char_rule": "仅使用中文汉字、数字、标点符号（禁止使用表情符号和特殊字符）",
    },
}


def generate_script_from_news(
    news_item: dict,
    target_duration: int = 50,
    language: str = "ko",
) -> dict:
    """
    뉴스 기사를 바탕으로 YouTube Shorts 대본을 생성한다.

    Args:
        news_item: {"source", "title", "summary", "url", "published"}
        target_duration: 목표 영상 길이 (초)
        language: 대본 언어 코드 ("ko" | "ja" | "zh")
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)
    segment_count = max(4, min(7, target_duration // 8))
    lc = _LANG_CONFIG.get(language, _LANG_CONFIG["ko"])

    prompt = f"""
당신은 AI/테크 뉴스를 명확하게 전달하는 뉴스 앵커형 YouTube Shorts 제작자입니다.
다음 뉴스를 바탕으로 {lc['instruction']}

뉴스 출처: {news_item.get('source', '')}
뉴스 제목: {news_item.get('title', '')}
뉴스 내용: {news_item.get('summary', '')}

핵심 요구사항:
- 총 {target_duration}초 분량 ({segment_count}개 세그먼트, 각 8~12초)
- 각 세그먼트 narration은 50~80자 (빠른 TTS 기준)
- {lc['char_rule']}
- 뉴스의 실제 내용과 수치, 사실을 정확하게 전달 (추측이나 과장 금지)
- 시청자가 영상 하나로 해당 뉴스를 완전히 이해할 수 있어야 함

세그먼트 구성:
1. 첫 세그먼트: 핵심 사실 한 줄 요약으로 시작 (무엇이 어떻게 됐는지)
2. 중간 세그먼트: 배경, 세부 내용, 수치, 영향 등 구체적 정보 전달
3. 마지막 세그먼트: 의미와 전망 정리, "{lc['closing']}"

image_prompt 기준:
- 뉴스 내용을 시각적으로 표현하는 영어 프롬프트
- 예) OpenAI 뉴스 → futuristic AI research lab, glowing neural networks, dark cinematic
      Claude 뉴스 → Anthropic logo, purple AI brain visualization, clean modern design
      Gemini 뉴스 → Google DeepMind research, colorful data streams, tech aesthetic

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "title": "{lc['title_hint']}",
  "description": "{lc['desc_hint']}",
  "tags": {lc['tags_hint']},
  "segments": [
    {{
      "narration": "{lc['narration_hint']}",
      "image_prompt": "Detailed English image prompt, vertical 9:16, cinematic quality, no text"
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    script = _parse_response(response.text, news_item.get("title", "뉴스"))
    print(f"[script_gen] 언어: {language}")
    return script


def generate_script(topic: str, target_duration: int = 50, language: str = "ko") -> dict:
    """
    주제(topic)를 받아 숏츠 대본 JSON을 반환한다.

    Args:
        topic: 영상 주제
        target_duration: 목표 영상 길이 (초)
        language: 대본 언어 코드 ("ko" | "ja" | "zh")
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)
    segment_count = max(4, min(7, target_duration // 8))
    lc = _LANG_CONFIG.get(language, _LANG_CONFIG["ko"])

    prompt = f"""
당신은 YouTube Shorts 전문 콘텐츠 제작자입니다.
아래 주제로 {lc['instruction']}

주제: {topic}
목표 영상 길이: {target_duration}초
세그먼트 수: {segment_count}개

요구사항:
- 각 세그먼트의 narration은 천천히 읽으면 8~12초 분량 (50~80자)
- 첫 세그먼트는 시청자의 흥미를 끄는 후킹 문장으로 시작
- 마지막 세그먼트는 "{lc['closing']}"
- {lc['char_rule']}
- image_prompt는 해당 내용을 표현하는 영어 이미지 설명 (Imagen AI용, 세부적이고 시각적으로)
- image_prompt는 반드시 9:16 세로 비율에 맞는 구도로 묘사

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "title": "{lc['title_hint']}",
  "description": "{lc['desc_hint']}",
  "tags": {lc['tags_hint']},
  "segments": [
    {{
      "narration": "{lc['narration_hint']}",
      "image_prompt": "Detailed English image prompt for AI image generation, vertical 9:16 portrait orientation, cinematic quality"
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return _parse_response(response.text, topic)


def _parse_response(raw_text: str, label: str) -> dict:
    """Gemini 응답 텍스트를 파싱해 스크립트 dict를 반환한다."""
    raw = raw_text.strip()

    # JSON 블록 추출 (```json ... ``` 형태 대응)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        script = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini 응답을 JSON으로 파싱 실패: {e}\n원문:\n{raw}")

    required_keys = {"title", "description", "tags", "segments"}
    missing = required_keys - set(script.keys())
    if missing:
        raise ValueError(f"대본 JSON에 필수 키가 없습니다: {missing}")

    print(f"[script_gen] 대본 생성 완료 - '{script['title']}' ({len(script['segments'])}개 세그먼트)")
    return script
