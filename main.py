"""
YouTube Shorts 자동 생성기
사용법:
    python main.py once              # 뉴스 1개로 영상 즉시 생성 (테스트)
    python main.py schedule          # 스케줄러 시작 (config의 interval_hours 기준)
    python main.py list              # 생성된 영상 목록 + DB 통계
    python main.py web               # Supabase에서 다음 주제 자동 선택 후 실행
    python main.py web <topic_id>    # Supabase의 특정 주제 실행
"""
import os
import sys
import glob

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_single_video(cfg: dict, news_item: dict, lang_cfg: dict, channel_hint: str = "") -> str:
    """
    뉴스 1개 + 언어 설정으로 영상을 생성하고 경로를 반환한다.

    Args:
        cfg: config.yaml 전체 설정
        news_item: 뉴스 데이터 dict
        lang_cfg: config.yaml의 languages 항목 1개
                  {"code": "ko", "name": "한국어", "tts_voice": ..., "font_path": ..., "watermark": ...}
        channel_hint: 채널/주제 이름 (마지막 멘트에 반영)
    """
    from src.script_gen import generate_script_from_news
    from src.image_gen import generate_image
    from src.tts_gen import generate_tts
    from src.video_maker import make_video, generate_output_filename
    from src.uploader import upload_all

    lang_code  = lang_cfg.get("code", "ko")
    lang_name  = lang_cfg.get("name", lang_code)
    tts_voice  = lang_cfg.get("tts_voice")
    font_path  = lang_cfg.get("font_path")
    watermark  = lang_cfg.get("watermark", "AI뉴스 구독")

    temp_dir     = cfg.get("temp_dir", "temp")
    output_dir   = cfg.get("output_dir", "output")
    video_cfg    = cfg.get("video", {})
    subtitle_cfg = cfg.get("subtitle", {})
    bgm_cfg      = cfg.get("bgm", {})
    tts_cfg      = cfg.get("tts", {})
    resolution   = tuple(video_cfg.get("resolution", [1080, 1920]))
    fps          = video_cfg.get("fps", 30)
    target_dur   = video_cfg.get("target_duration", 50)

    # 언어별 임시 파일 디렉터리 분리 (동시 생성 시 충돌 방지)
    lang_temp = os.path.join(temp_dir, lang_code)
    os.makedirs(lang_temp, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[{lang_name}] 대본 생성 중...")

    # 1. 대본 생성 (해당 언어로)
    if news_item.get("_is_ai"):
        from src.script_gen import generate_script
        script = generate_script(
            topic=f"{news_item['title']}\n\n{news_item.get('summary', '')}",
            target_duration=target_dur,
            language=lang_code,
            channel_hint=channel_hint,
        )
    else:
        script = generate_script_from_news(
            news_item,
            target_duration=target_dur,
            language=lang_code,
            channel_hint=channel_hint,
        )

    # 2. 세그먼트별 이미지 + 음성
    segments = []
    for i, seg in enumerate(script["segments"]):
        print(f"[{lang_name}] 세그먼트 {i+1}/{len(script['segments'])} 생성 중...")
        img = generate_image(prompt=seg["image_prompt"], size=resolution)

        audio_path = os.path.join(lang_temp, f"seg_{i:02d}.mp3")
        generate_tts(
            text=seg["narration"],
            output_path=audio_path,
            language=lang_code,
            voice=tts_voice or tts_cfg.get("voice"),
            speed=tts_cfg.get("speed"),
        )

        segments.append({
            "image": img,
            "audio_path": audio_path,
            "narration": seg["narration"],
        })

    # 3. 영상 조합 (언어 코드를 파일명에 포함)
    output_path = generate_output_filename(script["title"], output_dir, suffix=lang_code)
    make_video(
        segments=segments,
        output_path=output_path,
        subtitle_cfg=subtitle_cfg,
        bgm_cfg=bgm_cfg,
        fps=fps,
        watermark_text=watermark,
        font_path=font_path,
    )

    # 4. 전체 SNS 업로드 (YouTube는 언어·지역 제한 적용)
    yt_token     = lang_cfg.get("_yt_token_json")
    yt_secret    = lang_cfg.get("_yt_client_secret_json")
    upload_all(
        video_path=output_path,
        title=script["title"],
        description=script["description"],
        tags=script["tags"],
        cfg=cfg,
        lang_cfg=lang_cfg,
        yt_token_json=yt_token,
        yt_client_secret_json=yt_secret,
    )

    return output_path


def run_multilingual_videos(cfg: dict, news_item: dict) -> list[str]:
    """
    뉴스 1개로 config의 languages 설정에 따라 다국어 영상을 모두 생성하고
    업로드한다.

    Returns:
        생성된 영상 경로 리스트
    """
    languages = cfg.get("languages", [{"code": "ko", "name": "한국어"}])
    paths = []

    print(f"\n{'='*55}")
    print(f"[다국어 생성] {len(languages)}개 언어: {', '.join(l['name'] for l in languages)}")
    print(f"  뉴스: [{news_item['source']}] {news_item['title'][:45]}...")
    print(f"{'='*55}")

    for lang_cfg in languages:
        lang_name = lang_cfg.get("name", lang_cfg.get("code"))
        print(f"\n{'─'*50}")
        print(f"[{lang_name}] 시작")
        print(f"{'─'*50}")
        try:
            path = run_single_video(cfg, news_item, lang_cfg)
            paths.append(path)
            print(f"[{lang_name}] 완료: {os.path.basename(path)}")
        except Exception as e:
            print(f"[{lang_name}] 실패: {e}")

    return paths


def cmd_once(cfg: dict):
    """뉴스 1개로 다국어 영상 즉시 생성."""
    from src.news_fetcher import fetch_news
    from src.db import save_posted

    news_list = fetch_news(max_count=1, skip_processed=True)
    if not news_list:
        print("새로운 뉴스가 없습니다. 모든 뉴스가 이미 처리됐습니다.")
        return

    news = news_list[0]
    paths = run_multilingual_videos(cfg, news)

    if paths:
        save_posted(news, paths[0])  # 뉴스 중복 방지는 1회만 기록

    print(f"\n{'='*55}")
    print(f"완료: {len(paths)}개 영상 생성")
    for p in paths:
        print(f"  {os.path.basename(p)}")
    print(f"{'='*55}\n")


def cmd_schedule(cfg: dict):
    """스케줄러 시작 — 매 interval_hours 시간마다 뉴스 1개 다국어 영상 생성."""
    from src.scheduler import start_scheduler
    from src.news_fetcher import fetch_news
    from src.db import save_posted

    schedule_cfg   = cfg.get("schedule", {})
    interval_hours = schedule_cfg.get("interval_hours", 6)
    daily_limit    = schedule_cfg.get("daily_limit", 4)
    start_time     = schedule_cfg.get("start_time", "09:00")

    def pipeline():
        from src.db import get_stats
        today_count = get_stats()["today"]
        if today_count >= daily_limit:
            print(f"[scheduler] 오늘 이미 {today_count}개 생성 완료 (한도: {daily_limit}개), 내일 재개")
            return

        news_list = fetch_news(max_count=1, skip_processed=True)
        if not news_list:
            print("[scheduler] 새로운 뉴스 없음, 다음 실행 대기 중...")
            return
        news = news_list[0]
        try:
            paths = run_multilingual_videos(cfg, news)
            if paths:
                save_posted(news, paths[0])
            print(f"[scheduler] 오늘 {today_count + 1}/{daily_limit}개 완료 ({len(paths)}개 언어)")
        except Exception as e:
            print(f"[scheduler] 영상 생성 실패: {e}")

    start_scheduler(pipeline, interval_hours=interval_hours, start_time=start_time)


def cmd_list(cfg: dict):
    """생성된 영상 목록 + DB 통계 출력."""
    from src.db import get_stats

    output_dir = cfg.get("output_dir", "output")
    videos = sorted(glob.glob(os.path.join(output_dir, "*.mp4")), reverse=True)

    stats = get_stats()
    print(f"\n[DB 통계]")
    print(f"  오늘 생성: {stats['today']}개 / 누적: {stats['total']}개")
    if stats["recent"]:
        print(f"  최근 영상:")
        for r in stats["recent"]:
            print(f"    [{r['source']}] {r['title'][:35]}  ({r['created_at']})")

    print(f"\n[파일 목록] {len(videos)}개")
    for v in videos[:10]:
        size_mb = os.path.getsize(v) / 1024 / 1024
        print(f"  {os.path.basename(v)}  ({size_mb:.1f} MB)")


def cmd_web(cfg: dict, topic_id: str = None):
    """Supabase 주제 기반 다중 채널 영상 생성 + 업로드."""
    from src.supabase_client import (
        get_next_topic, get_topic_youtube_token,
        save_video_result, mark_news_posted, get_posted_urls, update_last_run,
    )
    from src.news_fetcher import fetch_news

    topic = get_next_topic(topic_id)
    if not topic:
        print("[web] 실행할 주제가 없습니다 (active 주제 없음).")
        return

    print(f"\n[web] 주제: {topic['name']} (id: {topic['id']})")

    # 주제별 config 오버라이드 (없으면 config.yaml 기본값 사용)
    topic_cfg = {**cfg, **topic.get("config", {})}
    languages  = topic_cfg.get("languages", cfg.get("languages", [{"code": "ko", "name": "한국어"}]))
    keywords   = topic.get("keywords") or []

    # YouTube 토큰 로드 (주제별)
    yt_tokens = get_topic_youtube_token(topic["id"])
    if not yt_tokens:
        print(f"[web] YouTube 계정이 연결되지 않았습니다 (topic_id: {topic['id']}). 업로드 건너뜀.")
        yt_token_json, yt_client_secret_json = None, None
    else:
        yt_token_json, yt_client_secret_json = yt_tokens
        print(f"[web] YouTube 토큰 로드 완료")

    # 이 주제에서 이미 처리된 URL/제목 집합
    posted_urls = get_posted_urls(topic["id"])

    # 콘텐츠 모드 분기
    content_mode = topic.get("config", {}).get("content_mode", "news")

    if content_mode == "ai_prompt":
        from src.content_generator import pick_ai_topic
        ai_prompt = topic.get("config", {}).get("ai_prompt", "")
        if not ai_prompt:
            print(f"[web] [{topic['name']}] ai_prompt가 설정되지 않았습니다.")
            return
        topic_idea = pick_ai_topic(ai_prompt, exclude_titles=posted_urls)
        if not topic_idea:
            print(f"[web] [{topic['name']}] 새로운 AI 주제 없음.")
            return
        news = {
            "source": "AI생성",
            "title": topic_idea["title"],
            "summary": topic_idea.get("summary", ""),
            "url": f"ai://{topic_idea['title']}",
            "_is_ai": True,
        }
    else:
        # 뉴스 가져오기 (주제 키워드 적용)
        news_list = fetch_news(
            max_count=1,
            skip_processed=True,
            exclude_urls=posted_urls,
            keywords=keywords or None,
        )
        if not news_list:
            print(f"[web] [{topic['name']}] 새로운 뉴스 없음.")
            return
        news = news_list[0]

    # 언어별 영상 생성 (YouTube 토큰을 lang_cfg에 임시 주입)
    paths = []
    for lang_cfg in languages:
        lang_name = lang_cfg.get("name", lang_cfg.get("code"))
        print(f"\n{'─'*50}")
        print(f"[{lang_name}] 시작")
        print(f"{'─'*50}")
        # 토큰을 lang_cfg에 주입 (uploader로 전달)
        lang_cfg_with_token = {
            **lang_cfg,
            "_yt_token_json": yt_token_json,
            "_yt_client_secret_json": yt_client_secret_json,
        }
        try:
            path = run_single_video(topic_cfg, news, lang_cfg_with_token, channel_hint=topic.get("name", ""))
            paths.append((path, lang_cfg.get("code", "ko")))
            print(f"[{lang_name}] 완료: {os.path.basename(path)}")

            # 영상 이력 저장 (언어별)
            save_video_result(
                topic_id=topic["id"],
                news_url=news.get("url", ""),
                news_title=news.get("title", ""),
                language=lang_cfg.get("code", "ko"),
                title=os.path.basename(path),
                youtube_url="",  # uploader에서 반환값 받으면 업데이트 필요
            )
        except Exception as e:
            print(f"[{lang_name}] 실패: {e}")

    # 뉴스 처리 완료 표시
    if paths:
        mark_news_posted(topic["id"], news.get("url", ""))

    # 마지막 실행 시각 업데이트
    update_last_run(topic["id"])

    print(f"\n{'='*55}")
    print(f"[web] 완료: {topic['name']} — {len(paths)}개 영상 생성")
    for path, lang in paths:
        print(f"  [{lang}] {os.path.basename(path)}")
    print(f"{'='*55}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if not os.path.exists("config.yaml"):
        print("오류: config.yaml 파일이 없습니다.")
        sys.exit(1)

    cfg = load_config("config.yaml")

    # DB 초기화 (항상)
    from src.db import init_db
    init_db()

    if cmd == "web":
        topic_id = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_web(cfg, topic_id=topic_id)
        return

    commands = {
        "once":     cmd_once,
        "schedule": cmd_schedule,
        "list":     cmd_list,
    }

    if cmd not in commands:
        print(f"알 수 없는 명령어: {cmd}")
        print(__doc__)
        sys.exit(1)

    commands[cmd](cfg)


if __name__ == "__main__":
    main()
