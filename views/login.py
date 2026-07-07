"""ログイン・新規登録画面"""
import streamlit as st

from modules.auth import register_user, login_user
from config.settings import APP_NAME, APP_VERSION


def show_login():
    """未ログイン時に表示するログイン・新規登録画面"""
    st.markdown(
        f"""
        <div style="text-align:center; padding:48px 0 24px;">
            <div style="font-size:56px;">💳</div>
            <h1 style="font-size:26px; font-weight:700; margin:8px 0 4px;">{APP_NAME}</h1>
            <p style="color:#888; font-size:13px; margin:0;">Ver.{APP_VERSION}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.6, 1])

    with center:
        tab_login, tab_register = st.tabs(["🔑 ログイン", "📝 新規登録"])

        with tab_login:
            _login_form()

        with tab_register:
            _register_form()


def _login_form():
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "メールアドレス",
            placeholder="example@email.com",
            autocomplete="email",
        )
        password = st.text_input(
            "パスワード",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "ログイン", type="primary", use_container_width=True
        )

    if submitted:
        with st.spinner("認証中..."):
            ok, user, msg = login_user(email, password)
        if ok:
            st.session_state["user_id"]    = user["id"]
            st.session_state["user_name"]  = user["name"]
            st.session_state["user_email"] = user["email"]
            st.rerun()
        else:
            st.error(f"❌ {msg}")


def _register_form():
    with st.form("register_form", clear_on_submit=False):
        name = st.text_input("お名前", placeholder="例：山田 太郎")
        email = st.text_input(
            "メールアドレス",
            placeholder="example@email.com",
            autocomplete="email",
        )
        password = st.text_input(
            "パスワード（8文字以上）",
            type="password",
            autocomplete="new-password",
        )
        password2 = st.text_input(
            "パスワード（確認）",
            type="password",
            autocomplete="new-password",
        )
        submitted = st.form_submit_button(
            "アカウントを作成", type="primary", use_container_width=True
        )

    if submitted:
        if password != password2:
            st.error("❌ パスワードが一致しません")
        else:
            with st.spinner("登録中..."):
                ok, msg = register_user(name, email, password)
            if ok:
                st.success(f"✅ {msg}　左の「ログイン」タブからログインしてください。")
            else:
                st.error(f"❌ {msg}")
