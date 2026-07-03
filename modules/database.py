import sqlite3
import pandas as pd
from contextlib import contextmanager
from datetime import date, datetime
from config.settings import DB_PATH, DATA_DIR


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS payments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                year        INTEGER NOT NULL,
                month       INTEGER NOT NULL,
                payee       TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                payment_type TEXT   NOT NULL DEFAULT 'fixed',
                payment_day INTEGER,
                adjusted_date TEXT,
                amount      REAL    DEFAULT 0,
                payment_method TEXT DEFAULT '',
                status      TEXT    DEFAULT 'unpaid',
                category    TEXT    DEFAULT '',
                notes       TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                updated_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payment_templates (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                payee        TEXT    NOT NULL,
                description  TEXT    DEFAULT '',
                payment_type TEXT    NOT NULL DEFAULT 'fixed',
                payment_day  INTEGER,
                amount       REAL    DEFAULT 0,
                payment_method TEXT  DEFAULT '',
                category     TEXT    DEFAULT '',
                notes        TEXT    DEFAULT '',
                is_active    INTEGER DEFAULT 1,
                created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_payments_ym
                ON payments(year, month);
            CREATE INDEX IF NOT EXISTS idx_payments_status
                ON payments(status);
            CREATE INDEX IF NOT EXISTS idx_payments_payee
                ON payments(payee);
        """)


@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── 支払いCRUD ──────────────────────────────────────────────

def add_payment(data: dict) -> int:
    sql = """
        INSERT INTO payments
            (year, month, payee, description, payment_type,
             payment_day, adjusted_date, amount, payment_method,
             status, category, notes)
        VALUES
            (:year, :month, :payee, :description, :payment_type,
             :payment_day, :adjusted_date, :amount, :payment_method,
             :status, :category, :notes)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, data)
        return cur.lastrowid


def update_payment(payment_id: int, data: dict) -> None:
    data["id"] = payment_id
    data["updated_at"] = datetime.now().isoformat()
    sql = """
        UPDATE payments SET
            payee          = :payee,
            description    = :description,
            payment_type   = :payment_type,
            payment_day    = :payment_day,
            adjusted_date  = :adjusted_date,
            amount         = :amount,
            payment_method = :payment_method,
            status         = :status,
            category       = :category,
            notes          = :notes,
            updated_at     = :updated_at
        WHERE id = :id
    """
    with get_connection() as conn:
        conn.execute(sql, data)


def update_payment_status(payment_id: int, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE payments SET status=?, updated_at=? WHERE id=?",
            (status, datetime.now().isoformat(), payment_id),
        )


def delete_payment(payment_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM payments WHERE id=?", (payment_id,))


def get_payment(payment_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM payments WHERE id=?", (payment_id,)
        ).fetchone()
    return dict(row) if row else None


def get_payments_df(
    year: int,
    month: int,
    status_filter: str = "all",
    search: str = "",
    sort_col: str = "adjusted_date",
    sort_asc: bool = True,
) -> pd.DataFrame:
    where_clauses = ["year=? AND month=?"]
    params: list = [year, month]

    if status_filter == "unpaid":
        where_clauses.append("status='unpaid'")
    elif status_filter == "paid":
        where_clauses.append("status='paid'")
    elif status_filter == "overdue":
        today = date.today().isoformat()
        where_clauses.append(f"status='unpaid' AND adjusted_date < '{today}'")
    elif status_filter == "due_soon":
        today = date.today().isoformat()
        from datetime import timedelta
        soon = (date.today() + timedelta(days=3)).isoformat()
        where_clauses.append(
            f"status='unpaid' AND adjusted_date >= '{today}' AND adjusted_date <= '{soon}'"
        )

    if search:
        where_clauses.append(
            "(payee LIKE ? OR description LIKE ? OR category LIKE ?)"
        )
        like = f"%{search}%"
        params += [like, like, like]

    where_sql = " AND ".join(where_clauses)
    valid_cols = {
        "adjusted_date", "payee", "amount", "status", "payment_day",
        "payment_type", "category", "payment_method"
    }
    order_col = sort_col if sort_col in valid_cols else "adjusted_date"
    order_dir = "ASC" if sort_asc else "DESC"

    sql = f"""
        SELECT
            id, year, month, payee, description, payment_type,
            payment_day, adjusted_date, amount, payment_method,
            status, category, notes, created_at, updated_at
        FROM payments
        WHERE {where_sql}
        ORDER BY {order_col} {order_dir}, id ASC
    """
    with get_connection() as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df


def get_all_payees() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT payee FROM payments ORDER BY payee"
        ).fetchall()
    return [r[0] for r in rows]


def get_all_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM payments WHERE category != '' ORDER BY category"
        ).fetchall()
    return [r[0] for r in rows]


# ─── ダッシュボード集計 ────────────────────────────────────────

def get_dashboard_stats(year: int, month: int) -> dict:
    today = date.today().isoformat()
    week_start = date.today().isoformat()
    from datetime import timedelta
    week_end = (date.today() + timedelta(days=6)).isoformat()

    with get_connection() as conn:
        def scalar(sql, params=()):
            row = conn.execute(sql, params).fetchone()
            return row[0] if row and row[0] is not None else 0

        total_count = scalar(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=?",
            (year, month),
        )
        total_amount = scalar(
            "SELECT SUM(amount) FROM payments WHERE year=? AND month=?",
            (year, month),
        )
        paid_amount = scalar(
            "SELECT SUM(amount) FROM payments WHERE year=? AND month=? AND status='paid'",
            (year, month),
        )
        unpaid_count = scalar(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND status='unpaid'",
            (year, month),
        )
        unpaid_amount = scalar(
            "SELECT SUM(amount) FROM payments WHERE year=? AND month=? AND status='unpaid'",
            (year, month),
        )
        overdue_count = scalar(
            f"SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND status='unpaid' AND adjusted_date < '{today}'",
            (year, month),
        )
        this_week_count = scalar(
            f"SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND adjusted_date >= '{week_start}' AND adjusted_date <= '{week_end}'",
            (year, month),
        )
        fixed_count = scalar(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND payment_type='fixed'",
            (year, month),
        )
        variable_count = scalar(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND payment_type='variable'",
            (year, month),
        )
        paid_count = scalar(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=? AND status='paid'",
            (year, month),
        )

    return {
        "total_count": total_count,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
        "unpaid_amount": unpaid_amount,
        "overdue_count": overdue_count,
        "this_week_count": this_week_count,
        "fixed_count": fixed_count,
        "variable_count": variable_count,
    }


def get_monthly_summary(year: int) -> pd.DataFrame:
    sql = """
        SELECT
            month,
            COUNT(*) as count,
            SUM(amount) as total,
            SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as paid,
            SUM(CASE WHEN status='unpaid' THEN amount ELSE 0 END) as unpaid
        FROM payments
        WHERE year=?
        GROUP BY month
        ORDER BY month
    """
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(year,))


def get_all_payments_df(year: int) -> pd.DataFrame:
    sql = """
        SELECT * FROM payments WHERE year=?
        ORDER BY month, adjusted_date, id
    """
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(year,))


# ─── 翌月繰り越し ───────────────────────────────────────────────

def rollover_to_next_month(year: int, month: int, include_variable: bool = False) -> int:
    from modules.holiday import adjust_payment_date

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    # 次月にすでにデータがある場合はスキップ
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=?",
            (next_year, next_month),
        ).fetchone()[0]

    if existing > 0:
        return 0

    with get_connection() as conn:
        if include_variable:
            rows = conn.execute(
                "SELECT * FROM payments WHERE year=? AND month=?",
                (year, month),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM payments WHERE year=? AND month=? AND payment_type='fixed'",
                (year, month),
            ).fetchall()

    count = 0
    for row in rows:
        r = dict(row)
        adj = adjust_payment_date(next_year, next_month, r.get("payment_day") or 1)
        data = {
            "year": next_year,
            "month": next_month,
            "payee": r["payee"],
            "description": r["description"],
            "payment_type": r["payment_type"],
            "payment_day": r["payment_day"],
            "adjusted_date": adj.isoformat() if adj else None,
            "amount": r["amount"],
            "payment_method": r["payment_method"],
            "status": "unpaid",
            "category": r["category"],
            "notes": r["notes"],
        }
        add_payment(data)
        count += 1

    return count


def get_rollover_candidates(year: int, month: int) -> pd.DataFrame:
    """翌月繰り越し対象（固定・固定変動）を返す"""
    from config.settings import ROLLOVER_TYPES
    placeholders = ",".join("?" * len(ROLLOVER_TYPES))
    sql = f"""
        SELECT * FROM payments
        WHERE year=? AND month=?
          AND payment_type IN ({placeholders})
        ORDER BY adjusted_date, payee
    """
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=(year, month, *ROLLOVER_TYPES))


def check_next_month_exists(next_year: int, next_month: int) -> int:
    """翌月の既存データ件数を返す"""
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM payments WHERE year=? AND month=?",
            (next_year, next_month),
        ).fetchone()[0]


def execute_rollover(next_year: int, next_month: int, items: list[dict]) -> int:
    """
    確認済みのアイテムリストを翌月に登録する。
    items: {"payee", "description", "payment_type", "payment_day",
             "amount", "payment_method", "category", "notes"} の dict リスト
    """
    from modules.holiday import adjust_payment_date
    count = 0
    for item in items:
        adj = adjust_payment_date(next_year, next_month, item.get("payment_day") or 1)
        data = {
            "year": next_year,
            "month": next_month,
            "payee": item["payee"],
            "description": item["description"],
            "payment_type": item["payment_type"],
            "payment_day": item["payment_day"],
            "adjusted_date": adj.isoformat() if adj else None,
            "amount": item["amount"],
            "payment_method": item["payment_method"],
            "status": "unpaid",
            "category": item["category"],
            "notes": item["notes"],
        }
        add_payment(data)
        count += 1
    return count


# ─── テンプレートCRUD ────────────────────────────────────────

def get_templates_df() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM payment_templates WHERE is_active=1 ORDER BY payee",
            conn,
        )


def add_template(data: dict) -> int:
    sql = """
        INSERT INTO payment_templates
            (payee, description, payment_type, payment_day,
             amount, payment_method, category, notes)
        VALUES
            (:payee, :description, :payment_type, :payment_day,
             :amount, :payment_method, :category, :notes)
    """
    with get_connection() as conn:
        cur = conn.execute(sql, data)
        return cur.lastrowid


def delete_template(template_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE payment_templates SET is_active=0 WHERE id=?",
            (template_id,),
        )


# ─── 一括インポート ────────────────────────────────────────────

def bulk_insert_payments(payments: list[dict]) -> int:
    count = 0
    for data in payments:
        add_payment(data)
        count += 1
    return count
