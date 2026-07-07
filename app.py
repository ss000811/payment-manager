"""
支払い管理システム Ver.2.0
メインエントリポイント
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from modules.database import init_db
from utils.helpers import get_current_year_month
from config.settings import APP_NAME, APP_VERSION


# ─── ページ設定 ─────────────────────────────────────────────

st.set_page_config(
    page_title=f"{APP_NAME}",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"**{APP_NAME} {APP_VERSION}**\n\n毎月の支払い管理を効率化するビジネスツール",
    },
)

# ─── カスタムCSS ────────────────────────────────────────────

def load_css():
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

load_css()

# ─── DB初期化 ───────────────────────────────────────────────

init_db()

# ─── クラウド環境の検出・警告 ────────────────────────────────

def _is_cloud() -> bool:
    return os.environ.get("HOME", "") == "/home/appuser"

if _is_cloud():
    st.info(
        "**Supabase クラウドデータベースで動作しています。**  \n"
        "データはクラウドに永続保存されます。アプリのスリープ後もデータは保持されます。",
        icon="☁️",
    )

# ─── 未ログイン時はログイン画面のみ表示 ────────────────────────

if "user_id" not in st.session_state:
    from views.login import show_login
    show_login()
    st.stop()

# ─── セッション初期化（ログイン済みの場合のみ） ────────────────

if "view_year" not in st.session_state or "view_month" not in st.session_state:
    y, m = get_current_year_month()
    st.session_state.setdefault("view_year",  y)
    st.session_state.setdefault("view_month", m)

st.session_state.setdefault("current_page", "dashboard")
st.session_state.setdefault("selected_id",  None)
st.session_state.setdefault("refresh",      False)

if st.session_state.get("refresh"):
    st.session_state["refresh"] = False

# ─── サイドバーナビゲーション ────────────────────────────────

with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 12px 0 8px;">
            <div style="font-size:36px;">💳</div>
            <div style="color:#fff; font-size:16px; font-weight:700; margin-top:4px;">
                {APP_NAME}
            </div>
            <div style="color:rgba(255,255,255,0.6); font-size:11px;">Ver.{APP_VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ─ ログインユーザー情報
    user_name  = st.session_state.get("user_name",  "")
    user_email = st.session_state.get("user_email", "")
    st.markdown(
        f"""
        <div style="background:rgba(255,255,255,0.12); border-radius:8px;
                    padding:10px 12px; margin-bottom:8px;">
            <div style="color:#fff; font-size:13px; font-weight:600;">👤 {user_name}</div>
            <div style="color:rgba(255,255,255,0.55); font-size:11px; margin-top:2px;">
                {user_email}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ─ ログアウトボタン
    if st.button("🚪 ログアウト", use_container_width=True):
        try:
            from modules.supabase_client import get_supabase
            get_supabase().auth.sign_out()
        except Exception:
            pass
        for key in ["user_id", "user_name", "user_email",
                    "access_token", "refresh_token",
                    "view_year", "view_month", "tbl_gen",
                    "del_id", "del_payee", "del_amount",
                    "toast_msg", "refresh", "current_page", "selected_id"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.divider()

    page = st.radio(
        "ナビゲーション",
        options=["dashboard", "payment_list", "settings"],
        format_func=lambda x: {
            "dashboard":    "📊 ダッシュボード",
            "payment_list": "📋 支払い管理",
            "settings":     "⚙️ 設定・バックアップ",
        }[x],
        label_visibility="collapsed",
        key="nav_page",
    )

    st.divider()

    # ─ 現在の表示月
    vy = st.session_state.get("view_year")
    vm = st.session_state.get("view_month")
    st.markdown(
        f"""
        <div style="color:rgba(255,255,255,0.8); font-size:12px; text-align:center;">
            表示中：{vy}年{vm}月
        </div>
        """,
        unsafe_allow_html=True,
    )

    cy, cm = get_current_year_month()
    if (vy, vm) != (cy, cm):
        if st.button("📅 今月に戻る", use_container_width=True):
            st.session_state["view_year"]  = cy
            st.session_state["view_month"] = cm
            st.rerun()

    st.markdown(
        """
        <div style="color:rgba(255,255,255,0.4); font-size:10px; text-align:center; margin-top:20px;">
            © 2024 支払い管理システム
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─── ページルーティング ──────────────────────────────────────

if page == "dashboard":
    from views.dashboard import show_dashboard
    show_dashboard()

elif page == "payment_list":
    from views.payment_list import show_payment_list
    show_payment_list()

elif page == "settings":
    from views.settings_page import show_settings
    show_settings()
