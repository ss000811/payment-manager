"""共通ユーティリティ関数"""
from datetime import date, timedelta


def format_currency(amount) -> str:
    try:
        return f"¥{int(amount):,}"
    except (TypeError, ValueError):
        return "¥0"


def format_date_jp(date_str: str) -> str:
    """YYYY-MM-DD → YYYY年MM月DD日"""
    try:
        d = date.fromisoformat(date_str)
        return f"{d.year}年{d.month}月{d.day}日"
    except Exception:
        return date_str or ""


def get_current_year_month() -> tuple[int, int]:
    today = date.today()
    return today.year, today.month


def days_until(date_str: str) -> int | None:
    """今日から date_str までの日数（過去は負）"""
    try:
        d = date.fromisoformat(date_str)
        return (d - date.today()).days
    except Exception:
        return None


def get_effective_status(status: str, adjusted_date: str) -> str:
    """
    DBのstatusに加えて、adjusted_dateが過去なら"overdue"、
    3日以内なら"due_soon"を返す。支払済みはそのまま。
    """
    if status == "paid":
        return "paid"
    try:
        d = date.fromisoformat(adjusted_date)
    except Exception:
        return status
    today = date.today()
    if d < today:
        return "overdue"
    if d <= today + timedelta(days=3):
        return "due_soon"
    return "unpaid"


def status_label(effective_status: str) -> str:
    return {
        "paid": "✅ 支払済み",
        "overdue": "🔴 期限超過",
        "due_soon": "🟡 期限間近",
        "unpaid": "⬜ 未払い",
    }.get(effective_status, effective_status)


def status_color(effective_status: str) -> str:
    return {
        "paid": "#E8F5E9",
        "overdue": "#FFEBEE",
        "due_soon": "#FFF8E1",
        "unpaid": "#FFFFFF",
    }.get(effective_status, "#FFFFFF")


def status_text_color(effective_status: str) -> str:
    return {
        "paid": "#2E7D32",
        "overdue": "#C62828",
        "due_soon": "#E65100",
        "unpaid": "#1565C0",
    }.get(effective_status, "#000000")


def next_year_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def prev_year_month(year: int, month: int) -> tuple[int, int]:
    if month == 1:
        return year - 1, 12
    return year, month - 1
