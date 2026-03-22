"""
AI 프롬프트 기반 콘텐츠 주제 생성기.
Gemini를 사용해 중복되지 않는 새로운 주제를 선정한다.
"""
import json
import os
import re

from google import genai


def pick_ai_topic(prompt: str, exclude_titles: set[str]) -> dict | None:
    """
    사용자 프롬프트를 바탕으로 Gemini가 새로운 콘텐츠 주제를 선정한다.

    Args:
        prompt: 사용자가 설정한 콘텐츠 방향 프롬프트
        exclude_titles: 이미 사용된 주제 제목 집합 (중복 방지)

    Returns:
        {"title": str, "summary": str} 또는 None
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    exclude_list = "\n".join(f"- {t}" for t in list(exclude_titles)[-50:]) if exclude_titles else "없음"

    system_prompt = f"""당신은 YouTube Shorts 콘텐츠 기획자입니다.
아래 콘텐츠 방향에 맞는 새로운 영상 주제를 10개 제안하세요.

콘텐츠 방향:
{prompt}

이미 사용된 주제 (반드시 제외):
{exclude_list}

요구사항:
- 각 주제는 구체적이고 시청자가 흥미를 가질 만한 것
- 이미 사용된 주제와 겹치지 않을 것
- 유튜브 쇼츠 (60초) 분량에 적합할 것

반드시 아래 JSON 형식으로만 응답하세요:

{{
  "topics": [
    {{"title": "주제 제목", "summary": "주제에 대한 2~3문장 설명"}},
    ...
  ]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=system_prompt,
    )

    raw = response.text.strip()
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if json_match:
        raw = json_match.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini 응답 파싱 실패: {e}\n원문:\n{raw}")

    topics = data.get("topics", [])

    # 이미 사용된 주제 필터링 (정확 일치 + 유사 방지)
    exclude_lower = {t.lower() for t in exclude_titles}
    for topic in topics:
        title = topic.get("title", "")
        if title and title.lower() not in exclude_lower:
            print(f"[content_generator] 선정된 주제: {title}")
            return topic

    print("[content_generator] 사용 가능한 새 주제가 없습니다.")
    return None
