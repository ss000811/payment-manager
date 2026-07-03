"""日本の祝日・営業日計算モジュール"""
from datetime import date, timedelta

try:
    import jpholiday
    _HAS_JPHOLIDAY = True
except ImportError:
    _HAS_JPHOLIDAY = False


def is_holiday(d: date) -> bool:
    """土日または祝日かどうかを判定"""
    if d.weekday() >= 5:  # 土曜=5, 日曜=6
        return True
    if _HAS_JPHOLIDAY:
        return jpholiday.is_holiday(d)
    return False


def is_business_day(d: date) -> bool:
    return not is_holiday(d)


def next_business_day(d: date) -> date:
    """翌営業日を返す（土日祝をスキップ）"""
    candidate = d
    while is_holiday(candidate):
        candidate += timedelta(days=1)
    return candidate


def adjust_payment_date(year: int, month: int, day: int) -> date:
    """
    指定年月の payment_day を実際の日付に変換し、
    土日祝の場合は翌営業日に調整して返す。
    月末を超える日はその月の最終日に丸める。
    """
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    actual_day = min(day, last_day)
    d = date(year, month, actual_day)
    return next_business_day(d)


def get_holiday_name(d: date) -> str | None:
    """祝日名を返す（祝日でなければ None）"""
    if not _HAS_JPHOLIDAY:
        return None
    return jpholiday.is_holiday_name(d) or None


def list_holidays_in_month(year: int, month: int) -> list[tuple[date, str]]:
    """指定月内の祝日一覧を返す"""
    if not _HAS_JPHOLIDAY:
        return []
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    result = []
    for day in range(1, last_day + 1):
        d = date(year, month, day)
        name = jpholiday.is_holiday_name(d)
        if name:
            result.append((d, name))
    return result
