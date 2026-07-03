"""入力バリデーション"""
import calendar
from config.settings import PAYMENT_METHODS


def validate_payment_form(data: dict) -> tuple[bool, list[str]]:
    errors = []

    if not data.get("payee", "").strip():
        errors.append("支払先は必須です。")

    try:
        day = int(data.get("payment_day", 0))
        if not (1 <= day <= 31):
            errors.append("支払日は1〜31の整数で入力してください。")
        year = int(data.get("year", 2024))
        month = int(data.get("month", 1))
        last_day = calendar.monthrange(year, month)[1]
        if day > last_day:
            errors.append(f"{year}年{month}月の最終日は{last_day}日です。支払日を修正してください。")
    except (TypeError, ValueError):
        errors.append("支払日は数値で入力してください。")

    try:
        amount = float(data.get("amount", 0) or 0)
        if amount < 0:
            errors.append("金額は0以上で入力してください。")
    except (TypeError, ValueError):
        errors.append("金額は数値で入力してください。")

    if data.get("payment_type") not in ("fixed", "variable"):
        errors.append("固定/変動の選択が無効です。")

    return len(errors) == 0, errors
