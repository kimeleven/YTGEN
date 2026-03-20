"""
YouTube Shorts 자동 생성기
사용법:
    python main.py once       # 뉴스 1개로 영상 즉시 생성 (테스트)
    python main.py schedule   # 스케줄러 시작 (config의 interval_hours 기준)
    python main.py list       # 생성된 영상 목록 + DB 통계
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


def run_single_video(cfg: dict, news_item: dict) -> str:
    """뉴스 1개로 영상을 생성하고 경로를 반환한다."""
    from src.script_gen import generate_script_from_news
    from src.image_gen import generate_image
    from src.tts_gen import generate_tts
    from src.video_maker import make_video, generate_output_filename
    from src.uploader import upload_to_youtube

    temp_dir     = cfg.get("temp_dir", "temp")
    output_dir   = cfg.get("output_dir", "output")
    video_cfg    = cfg.get("video", {})
    subtitle_cfg = cfg.get("subtitle", {})
    bgm_cfg      = cfg.get("bgm", {})
    tts_cfg      = cfg.get("tts", {})
    resolution   = tuple(video_cfg.get("resolution", [1080, 1920]))
    fps          = video_cfg.get("fps", 30)
    target_dur   = video_cfg.get("target_duration", 50)

    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n  뉴스: [{news_item['source']}] {news_item['title'][:50]}...")

    # 1. 대본 생성
    script = generate_script_from_news(news_item, target_duration=target_dur)

    # 2. 세그먼트별 이미지 + 음성
    segments = []
    for i, seg in enumerate(script["segments"]):
        img = generate_image(prompt=seg["image_prompt"], size=resolution)

        audio_path = os.path.join(temp_dir, f"seg_{i:02d}.mp3")
        generate_tts(
            text=seg["narration"],
            output_path=audio_path,
            voice=tts_cfg.get("voice"),
            speed=tts_cfg.get("speed"),
        )

        segments.append({
            "image": img,
            "audio_path": audio_path,
            "narration": seg["narration"],
        })

    # 3. 영상 조합
    output_path = generate_output_filename(script["title"], output_dir)
    make_video(
        segments=segments,
        output_path=output_path,
        subtitle_cfg=subtitle_cfg,
        bgm_cfg=bgm_cfg,
        fps=fps,
    )

    # 4. 업로드
    upload_to_youtube(
        video_path=output_path,
        title=script["title"],
        description=script["description"],
        tags=script["tags"],
    )

    return output_path


def cmd_once(cfg: dict):
    """뉴스 1개로 영상 즉시 생성."""
    from src.news_fetcher import fetch_news
    from src.db import save_posted

    news_list = fetch_news(max_count=1, skip_processed=True)
    if not news_list:
        print("새로운 뉴스가 없습니다. 모든 뉴스가 이미 처리됐습니다.")
        return

    news = news_list[0]
    print(f"\n{'='*55}")
    print(f"[단건 생성]")
    print(f"{'='*55}")

    path = run_single_video(cfg, news)
    save_posted(news, path)

    print(f"\n{'='*55}")
    print(f"완료: {path}")
    print(f"{'='*55}\n")


def cmd_schedule(cfg: dict):
    """스케줄러 시작 — 매 interval_hours 시간마다 뉴스 1개 영상 생성."""
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
            path = run_single_video(cfg, news)
            save_posted(news, path)
            print(f"[scheduler] 오늘 {today_count + 1}/{daily_limit}개 완료")
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
