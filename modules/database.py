"""Supabase を使った支払いデータ CRUD"""
import pandas as pd
from datetime import date, datetime

from modules.supabase_client import get_supabase

PAYMENT_INSERT_FIELDS = [
    "user_id", "year", "month", "payee", "description", "payment_type",
    "payment_day", "adjusted_date", "amount", "payment_method",
    "status", "category", "notes",
]


def init_db():
    """Supabase 接続確認（旧 SQLite 初期化の互換ラッパー）"""
    import streamlit as st
    try:
        get_supabase()
    except ValueError as e:
        st.error(f"❌ Supabase 接続設定エラー：{e}")
        st.code(
            "# .streamlit/secrets.toml に以下を追加してください:\n"
            'SUPABASE_URL = "https://your-project.supabase.co"\n'
            'SUPABASE_ANON_KEY = "your-anon-key"'
        )
        st.stop()


# ─── 支払いCRUD ──────────────────────────────────────────────

def add_payment(data: dict) -> str:
    client = get_supabase()
    insert = {k: data[k] for k in PAYMENT_INSERT_FIELDS if k in data}
    response = client.table("payments").insert(insert).execute()
    return response.data[0]["id"] if response.data else None


def update_payment(payment_id: str, data: dict) -> None:
    client = get_supabase()
    update = {k: data[k] for k in PAYMENT_INSERT_FIELDS if k in data and k != "user_id"}
    update["updated_at"] = datetime.now().isoformat()
    client.table("payments").update(update).eq("id", payment_id).execute()


def update_payment_status(payment_id: str, status: str, user_id: str) -> None:
    client = get_supabase()
    client.table("payments")\
        .update({"status": status, "updated_at": datetime.now().isoformat()})\
        .eq("id", payment_id)\
        .eq("user_id", user_id)\
        .execute()


def delete_payment(payment_id: str, user_id: str) -> None:
    client = get_supabase()
    client.table("payments")\
        .delete()\
        .eq("id", payment_id)\
        .eq("user_id", user_id)\
        .execute()


def get_payment(payment_id: str, user_id: str) -> dict | None:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("*")
        .eq("id", payment_id)
        .eq("user_id", user_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_payments_df(
    year: int,
    month: int,
    user_id: str,
    status_filter: str = "all",
    search: str = "",
    sort_col: str = "adjusted_date",
    sort_asc: bool = True,
) -> pd.DataFrame:
    client = get_supabase()
    query = (
        client.table("payments")
        .select("*")
        .eq("user_id", user_id)
        .eq("year", year)
        .eq("month", month)
    )

    if status_filter == "paid":
        query = query.eq("status", "paid")
    elif status_filter == "unpaid":
        query = query.eq("status", "unpaid")

    valid_cols = {
        "adjusted_date", "payee", "amount", "status",
        "payment_day", "payment_type", "category", "payment_method",
    }
    order_col = sort_col if sort_col in valid_cols else "adjusted_date"
    query = query.order(order_col, desc=not sort_asc)

    response = query.execute()
    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    today = date.today().isoformat()
    if status_filter == "overdue":
        adj = df["adjusted_date"].fillna("")
        df = df[(df["status"] == "unpaid") & (adj < today) & (adj != "")]
    elif status_filter == "due_soon":
        from datetime import timedelta
        soon = (date.today() + timedelta(days=3)).isoformat()
        adj = df["adjusted_date"].fillna("")
        df = df[(df["status"] == "unpaid") & (adj >= today) & (adj <= soon)]

    if search:
        mask = (
            df["payee"].str.contains(search, case=False, na=False) |
            df["description"].str.contains(search, case=False, na=False) |
            df["category"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    return df.reset_index(drop=True)


def get_all_payees(user_id: str) -> list[str]:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("payee")
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        return []
    return sorted(set(r["payee"] for r in response.data if r.get("payee")))


def get_all_categories(user_id: str) -> list[str]:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("category")
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        return []
    return sorted(set(r["category"] for r in response.data if r.get("category")))


# ─── ダッシュボード集計 ────────────────────────────────────────

def get_dashboard_stats(year: int, month: int, user_id: str) -> dict:
    from datetime import timedelta
    df = get_payments_df(year, month, user_id)

    zero = {
        "total_count": 0, "total_amount": 0.0, "paid_amount": 0.0,
        "paid_count": 0, "unpaid_count": 0, "unpaid_amount": 0.0,
        "overdue_count": 0, "this_week_count": 0,
        "fixed_count": 0, "variable_count": 0,
    }
    if df.empty:
        return zero

    today = date.today().isoformat()
    week_end = (date.today() + timedelta(days=6)).isoformat()
    adj = df["adjusted_date"].fillna("")

    paid_m = df["status"] == "paid"
    unpaid_m = df["status"] == "unpaid"
    overdue_m = unpaid_m & (adj < today) & (adj != "")
    week_m = (adj >= today) & (adj <= week_end)

    return {
        "total_count":     len(df),
        "total_amount":    float(df["amount"].sum()),
        "paid_amount":     float(df.loc[paid_m, "amount"].sum()),
        "paid_count":      int(paid_m.sum()),
        "unpaid_count":    int(unpaid_m.sum()),
        "unpaid_amount":   float(df.loc[unpaid_m, "amount"].sum()),
        "overdue_count":   int(overdue_m.sum()),
        "this_week_count": int(week_m.sum()),
        "fixed_count":     int((df["payment_type"] == "fixed").sum()),
        "variable_count":  int((df["payment_type"] == "variable").sum()),
    }


def get_monthly_summary(year: int, user_id: str) -> pd.DataFrame:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("month, amount, status")
        .eq("user_id", user_id)
        .eq("year", year)
        .execute()
    )
    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

    rows = []
    for m in sorted(df["month"].unique()):
        g = df[df["month"] == m]
        rows.append({
            "month":  int(m),
            "count":  len(g),
            "total":  float(g["amount"].sum()),
            "paid":   float(g.loc[g["status"] == "paid",   "amount"].sum()),
            "unpaid": float(g.loc[g["status"] == "unpaid", "amount"].sum()),
        })
    return pd.DataFrame(rows)


def get_all_payments_df(year: int, user_id: str) -> pd.DataFrame:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("*")
        .eq("user_id", user_id)
        .eq("year", year)
        .order("month")
        .order("adjusted_date")
        .execute()
    )
    if not response.data:
        return pd.DataFrame()
    df = pd.DataFrame(response.data)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df


# ─── 翌月繰り越し ───────────────────────────────────────────────

def get_rollover_candidates(year: int, month: int, user_id: str) -> pd.DataFrame:
    from config.settings import ROLLOVER_TYPES
    client = get_supabase()
    response = (
        client.table("payments")
        .select("*")
        .eq("user_id", user_id)
        .eq("year", year)
        .eq("month", month)
        .in_("payment_type", list(ROLLOVER_TYPES))
        .order("adjusted_date")
        .execute()
    )
    if not response.data:
        return pd.DataFrame()
    df = pd.DataFrame(response.data)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    return df


def check_next_month_exists(next_year: int, next_month: int, user_id: str) -> int:
    client = get_supabase()
    response = (
        client.table("payments")
        .select("id")
        .eq("user_id", user_id)
        .eq("year", next_year)
        .eq("month", next_month)
        .execute()
    )
    return len(response.data) if response.data else 0


def execute_rollover(
    next_year: int, next_month: int, items: list[dict], user_id: str
) -> int:
    from modules.holiday import adjust_payment_date
    rows = []
    for item in items:
        adj = adjust_payment_date(next_year, next_month, item.get("payment_day") or 1)
        rows.append({
            "user_id":        user_id,
            "year":           next_year,
            "month":          next_month,
            "payee":          item["payee"],
            "description":    item.get("description", ""),
            "payment_type":   item["payment_type"],
            "payment_day":    item.get("payment_day"),
            "adjusted_date":  adj.isoformat() if adj else None,
            "amount":         float(item.get("amount", 0) or 0),
            "payment_method": item.get("payment_method", ""),
            "status":         "unpaid",
            "category":       item.get("category", ""),
            "notes":          item.get("notes", ""),
        })

    if not rows:
        return 0

    client = get_supabase()
    response = client.table("payments").insert(rows).execute()
    return len(response.data) if response.data else 0


# ─── 一括インポート ────────────────────────────────────────────

def bulk_insert_payments(payments: list[dict]) -> int:
    if not payments:
        return 0
    insert_rows = [
        {k: p[k] for k in PAYMENT_INSERT_FIELDS if k in p}
        for p in payments
    ]
    client = get_supabase()
    response = client.table("payments").insert(insert_rows).execute()
    return len(response.data) if response.data else 0
