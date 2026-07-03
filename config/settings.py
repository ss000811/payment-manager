from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "payments.db"

APP_NAME = "支払い管理システム"
APP_VERSION = "1.0.0"

PAYMENT_METHODS = [
    "銀行振込",
    "口座引落",
    "クレジットカード",
    "現金",
    "電子マネー",
    "手形",
    "その他",
]

PAYMENT_TYPES = {
    "fixed": "固定（金額固定）",
    "fixed_variable": "固定（金額変動）",
    "variable": "変動",
}

# 翌月繰り越し対象になる payment_type 値
ROLLOVER_TYPES = ("fixed", "fixed_variable")

STATUS_OPTIONS = {
    "unpaid": "未払い",
    "paid": "支払済み",
}

CATEGORIES = [
    "家賃・賃貸",
    "光熱費",
    "通信費",
    "保険料",
    "税金・公課",
    "人件費",
    "業務委託費",
    "広告宣伝費",
    "仕入れ・原材料",
    "設備・機器費",
    "リース料",
    "サブスクリプション",
    "交通・運送費",
    "消耗品費",
    "その他",
]

DAYS_WARN_BEFORE = 3

STATUS_COLORS = {
    "paid": "#4CAF50",
    "unpaid": "#2196F3",
    "overdue": "#F44336",
    "due_soon": "#FF9800",
}

# CSV インポート時の列マッピング
CSV_COLUMN_MAP = {
    "支払先": "payee",
    "支払内容": "description",
    "固定変動": "payment_type",
    "支払日": "payment_day",
    "金額": "amount",
    "支払方法": "payment_method",
    "カテゴリ": "category",
    "備考": "notes",
}

CSV_PAYMENT_TYPE_MAP = {
    "固定": "fixed",
    "固定（金額固定）": "fixed",
    "固定（金額変動）": "fixed_variable",
    "変動": "variable",
    "fixed": "fixed",
    "fixed_variable": "fixed_variable",
    "variable": "variable",
}
