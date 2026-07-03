"""CSV インポート・エクスポートモジュール"""
import io
import csv
from datetime import date
import pandas as pd
from config.settings import CSV_COLUMN_MAP, CSV_PAYMENT_TYPE_MAP, PAYMENT_METHODS


EXPORT_COLUMNS = [
    ("payee", "支払先"),
    ("description", "支払内容"),
    ("payment_type_label", "固定変動"),
    ("payment_day", "支払日"),
    ("amount", "金額"),
    ("payment_method", "支払方法"),
    ("status_label", "ステータス"),
    ("category", "カテゴリ"),
    ("notes", "備考"),
    ("adjusted_date", "調整後支払日"),
]

STATUS_LABELS = {"paid": "支払済み", "unpaid": "未払い"}
TYPE_LABELS = {"fixed": "固定", "variable": "変動"}


def export_to_csv(df: pd.DataFrame) -> str:
    """DataFrameをCSV文字列に変換"""
    out = df.copy()
    out["payment_type_label"] = out["payment_type"].map(TYPE_LABELS).fillna(out["payment_type"])
    out["status_label"] = out["status"].map(STATUS_LABELS).fillna(out["status"])

    export_df = pd.DataFrame()
    for col, label in EXPORT_COLUMNS:
        if col in out.columns:
            export_df[label] = out[col]
        else:
            export_df[label] = ""

    return export_df.to_csv(index=False, encoding="utf-8-sig")


def import_from_csv(
    csv_content: bytes | str,
    year: int,
    month: int,
) -> tuple[list[dict], list[str]]:
    """
    CSVをパースして支払いデータのリストと警告リストを返す。
    Returns: (payments_list, warnings)
    """
    from modules.holiday import adjust_payment_date

    if isinstance(csv_content, bytes):
        for enc in ("utf-8-sig", "utf-8", "shift_jis", "cp932"):
            try:
                text = csv_content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("文字コードを自動判別できませんでした。UTF-8またはShift-JISで保存してください。")
    else:
        text = csv_content

    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]

    # 列名を内部キーにマップ（日本語列名 → 内部キー名）
    rename_map = {k: v for k, v in CSV_COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    required = ["payee"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が見つかりません: {', '.join(missing)}")

    payments = []
    warnings = []

    for i, row in df.iterrows():
        row_num = i + 2
        payee = str(row.get("payee", "")).strip()
        if not payee:
            warnings.append(f"行{row_num}: 支払先が空のためスキップしました。")
            continue

        p_type_raw = str(row.get("payment_type", "fixed")).strip()
        p_type = CSV_PAYMENT_TYPE_MAP.get(p_type_raw, "fixed")

        try:
            payment_day = int(float(row.get("payment_day", 1) or 1))
            payment_day = max(1, min(31, payment_day))
        except (ValueError, TypeError):
            payment_day = 1
            warnings.append(f"行{row_num}: 支払日を1日に設定しました。")

        try:
            amount = float(row.get("amount", 0) or 0)
        except (ValueError, TypeError):
            amount = 0
            warnings.append(f"行{row_num}: 金額を0に設定しました。")

        method = str(row.get("payment_method", "")).strip()
        if method and method not in PAYMENT_METHODS:
            warnings.append(f"行{row_num}: 支払方法「{method}」は非標準値です。")

        adj = adjust_payment_date(year, month, payment_day)

        payments.append({
            "year": year,
            "month": month,
            "payee": payee,
            "description": str(row.get("description", "")).strip(),
            "payment_type": p_type,
            "payment_day": payment_day,
            "adjusted_date": adj.isoformat() if adj else None,
            "amount": amount,
            "payment_method": method,
            "status": "unpaid",
            "category": str(row.get("category", "")).strip(),
            "notes": str(row.get("notes", "")).strip(),
        })

    return payments, warnings


def get_import_template_csv() -> str:
    """インポート用テンプレートCSVを返す"""
    headers = [label for _, label in CSV_COLUMN_MAP.items() if label != "ステータス"]
    sample = [
        ["株式会社サンプル", "事務所家賃", "固定", "25", "150000", "銀行振込", "家賃・賃貸", ""],
        ["電力会社", "電気代", "変動", "10", "30000", "口座引落", "光熱費", "概算金額"],
    ]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(list(CSV_COLUMN_MAP.values()))
    writer.writerows(sample)
    return "﻿" + buf.getvalue()  # UTF-8 BOM付き
