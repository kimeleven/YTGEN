"""
APScheduler를 사용해 주기적으로 영상을 생성/업로드한다.
interval_hours 간격으로 반복 실행.
"""
from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger


def start_scheduler(pipeline_fn, interval_hours: int = 1, start_time: str = "09:00"):
    """
    Args:
        pipeline_fn: 영상 1개를 생성하는 함수 (인자 없음)
        interval_hours: 실행 간격 (시간 단위, 기본 1시간)
        start_time: 첫 실행 시각 "HH:MM"
    """
    scheduler = BlockingScheduler(timezone="Asia/Seoul")

    # 첫 실행 시각 계산
    now = datetime.now()
    h, m = map(int, start_time.split(":"))
    first_run = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if first_run <= now:
        first_run += timedelta(days=1)

    trigger = IntervalTrigger(
        hours=interval_hours,
        start_date=first_run,
        timezone="Asia/Seoul",
    )

    scheduler.add_job(pipeline_fn, trigger, id="ytgen_job")

    print(f"[scheduler] 스케줄러 시작")
    print(f"  - 실행 간격: {interval_hours}시간마다 1개")
    print(f"  - 첫 실행: {first_run.strftime('%Y-%m-%d %H:%M')}")
    print(f"  - Ctrl+C로 종료")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[scheduler] 스케줄러 종료됨")
